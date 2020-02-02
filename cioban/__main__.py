#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A docker swarm service for automatically updating your services to the latest image tag push. """

import logging
import os
import sys
# import json
# import subprocess
import pygelf
import pause
import docker
from prometheus_client import start_http_server
from .lib import constants
from .lib import prometheus

FILENAME = os.path.splitext(sys.modules['__main__'].__file__)[0]


class Cioban():
    """ The main class """
    settings = {
        'filters': os.environ.get('FILTER_SERVICES', []),
        'blacklist': os.environ.get('BLACKLIST_SERVICES', []),
        'sleep_time': os.environ.get('SLEEP_TIME', '5m'),
        'prometheus_port': int(os.environ.get('PORT', 9308)),
        'timeout': int(os.environ.get('TIMEOUT', 60)),
    }

    def __init__(self):
        self.logging()

        prometheus.PROM_INFO.info({'version': constants.VERSION})
        if self.settings['filters']:
            self.logger.warning('FILTER_SERVICES="{}"'.format(self.settings['filters']))
            self.settings['filters'] = self.settings['filters'].split('=', 1)
            self.settings['filters'] = {self.settings['filters'][0]: self.settings['filters'][1]}
        else:
            self.logger.warning('FILTER_SERVICES is not set')

        if self.settings['blacklist']:
            self.logger.warning('BLACKLIST_SERVICES="{}"'.format(self.settings['blacklist']))
            self.settings['blacklist'] = self.settings['blacklist'].split(' ')
        else:
            self.logger.warning('BLACKLIST_SERVICES is not set')

        self.configure_sleep()
        self.logger.warning('SLEEP_TIME="{}"'.format(self.settings['sleep_time']))
        self.logger.warning('PORT="{}"'.format(self.settings['prometheus_port']))
        self.logger.warning('TIMEOUT={}'.format(self.settings['timeout']))

        self.run()

    def configure_sleep(self):
        """ converts 1w, 3d, 5h, 4m or 1s to something pause understands """
        relation = {
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks',
        }
        if any(s.isalpha() for s in self.settings['sleep_time']):
            self.sleep = int(self.settings['sleep_time'][:-1])
            if self.settings['sleep_time'][-1] in relation:
                self.sleep_type = relation[self.settings['sleep_time'][-1]]
            else:
                raise ValueError('{} not understood'.format(self.settings['sleep_time']))
        else:
            self.sleep = int(self.settings['sleep_time'])
            self.sleep_type = 'minutes'

    def run(self):
        """ prepares the run and then triggers it. this is the actual loop """
        self.logger.warning(
            "Starting {} {}-{} with prometheus metrics on port {}".format(
                __package__,
                constants.VERSION,
                constants.BUILD,
                self.settings['prometheus_port'],
            )
        )
        self.docker = docker.from_env()
        start_http_server(self.settings['prometheus_port'])  # starts the prometheus metrics server
        while True:
            prometheus.PROM_STATE_ENUM.state('running')
            self.logger.info('Starting update run')
            self._run()
            self.logger.info('Sleeping for {} {}'.format(self.sleep, self.sleep_type))
            prometheus.PROM_STATE_ENUM.state('sleeping')
            wait = getattr(pause, self.sleep_type)
            wait(self.sleep)

    def _update_image(self, image, image_sha):
        """ checks if an image has an update """
        registry_data = self.docker.images.get_registry_data(image)
        digest = registry_data.attrs['Descriptor']['digest']
        updated_image = '{}@{}'.format(image, digest)
        if image_sha == digest:
            updated_image = False
            self.logger.debug('{}@{}: No update available'.format(image, image_sha))

        return updated_image

    @prometheus.PROM_UPDATE_SUMMARY.time()
    def _run(self):
        """ the actual run """
        services = self.get_services()
        # prometheus metrics first
        for service in services:
            service_name = service.name
            try:
                prometheus.PROM_SVC_UPDATE_COUNTER.labels(service_name, service.id, service.short_id).inc(0)
            except docker.errors.NotFound as err:
                self.logger.error('Exception caught: {}'.format(err))
                self.logger.warning('Service {} disappeared. Reloading the service list.'.format(service_name))
                services = self.get_services()
        for service in services:
            image_with_digest = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
            image_parts = image_with_digest.split('@', 1)
            image = image_parts[0]
            image_sha = None

            # if there's no sha in the image name, restart the service _with_ sha
            try:
                image_sha = image_parts[1]
            except IndexError:
                pass

            update_image = self._update_image(image_sha=image_sha, image=image)
            if update_image:
                self.logger.info('Updating service {} with image {}'.format(service.name, update_image))
                service.update(image=update_image, force_update=True)

            updating = True
            while updating:
                try:
                    service.reload()
                except docker.errors.NotFound as err:
                    self.logger.error('Exception caught: {}'.format(err))
                    self.logger.warning('Service {} disappeared. Reloading the service list.'.format(service_name))
                    services = self.get_services()
                    break

                if service.attrs.get('UpdateStatus') and service.attrs['UpdateStatus'].get('State') == 'updating':
                    self.logger.info('Service {} is in status `updating`. Waiting 1s...'.format(service.name))
                    pause.seconds(1)
                else:
                    updating = False
            current_image = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
            if current_image == image_with_digest:
                self.logger.info('No updates for service {}'.format(service.name))
            else:
                self.logger.warning('Service {} has been updated'.format(service.name))
                prometheus.PROM_SVC_UPDATE_COUNTER.labels(service.name, service.id, service.short_id).inc(1)

    def logging(self):
        """ Configures the logging """
        self.logger = logging.getLogger(__package__)
        loglevel = os.environ.get('LOGLEVEL', 'WARNING')
        logging.basicConfig(
            stream=sys.stdout,
            level=loglevel,
            format='%(asctime)s.%(msecs)03d %(levelname)s {%(module)s} [%(funcName)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if os.environ.get('GELF_HOST'):
            GELF = pygelf.GelfUdpHandler(
                host=os.environ.get('GELF_HOST'),
                port=int(os.environ.get('GELF_PORT', 12201)),
                debug=True,
                include_extra_fields=True,
                _ix_id=FILENAME,
            )
            self.logger.addHandler(GELF)
            self.logger.warning('LOGLEVEL="{}"'.format(loglevel))
            self.logger.warning('Initialized logging with GELF enabled')

    def get_services(self):
        """ gets the list of services and filters out the black listed """
        services = self.docker.services.list(filters=self.settings['filters'])
        for blacklist_service in self.settings['blacklist']:
            for service in services:
                if service.name == blacklist_service:
                    self.logger.info('Blacklisted {}'.format(blacklist_service))
                    services.remove(service)
        return services


if __name__ == '__main__':
    cioban = Cioban()
