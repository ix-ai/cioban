#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A docker swarm service for automatically updating your services to the latest image tag push. """

import logging
import os
import sys
import json
import subprocess
import pygelf
import pause
import docker
from prometheus_client import start_http_server
import constants
import prometheus


class Cioban():
    """ The main class """
    settings = {
        'filters': os.environ.get('FILTER_SERVICES', []),
        'blacklist': os.environ.get('BLACKLIST_SERVICES', []),
        'sleep_time': os.environ.get('SLEEP_TIME', '5m'),
        'prometheus_port': int(os.environ.get('PORT', 9308)),
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

        if os.environ.get("VERBOSE"):
            self.logger.warning(constants.VERBOSE_DEPRECATION)
        if os.environ.get("DISABLE_HEARTBEAT"):
            self.logger.warning(constants.DISABLE_HEARTBEAT_DEPRECATION)

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
            "Starting cioban {} with prometheus metrics on port {}".format(
                constants.VERSION,
                self.settings['prometheus_port']
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

    def _update_service(self, service_id, image, service_name):
        """ updates a service to a specific image """
        self.logger.info('Trying to update service {} (id: {}) with image {}'.format(service_name, service_id, image))
        # Ideally this would work:
        #   service.update(image=image)
        # or:
        #   self.docker.api.update_service(
        #       service=service.id,
        #       version=service.version,
        #       fetch_current_spec=True,
        #       task_template=docker.types.TaskTemplate(service.attrs["Spec"]["TaskTemplate"]["ContainerSpec"]),
        #   )
        # but instead, we need to run (see https://github.com/docker/docker-py/issues/2422):
        try:
            update_run = subprocess.run(
                args=[
                    'docker',
                    'service',
                    'update',
                    '--with-registry-auth',
                    '--image={}'.format(image),
                    service_id
                ],
                capture_output=True,
            )
        except subprocess.CalledProcessError as err:
            self.logger.exception('Exception caught: {}'.format(err))
        else:
            if update_run.returncode > 0:
                self.logger.error('Command exited with return code {} for service {}'.format(
                    update_run.returncode,
                    service_name
                ))
            if update_run.stderr:
                self.logger.error('Command STDERR: {}'.format(update_run.stderr))
            if update_run.stdout:
                self.logger.debug('Command STDOUT: {}'.format(update_run.stdout))
        finally:
            self.logger.debug('Update command: {}'.format(json.dumps(update_run.args)))

    @prometheus.PROM_UPDATE_SUMMARY.time()
    def _run(self):
        """ the actual run """
        services = self.get_services()
        # prometheus metrics first
        for service in services:
            prometheus.PROM_SVC_UPDATE_COUNTER.labels(service.name, service.id, service.short_id).inc(0)
        for service in services:
            image_with_digest = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
            image = image_with_digest.split('@', 1)[0]
            self._update_service(service_id=service.id, image=image, service_name=service.name)
            updating = True
            while updating:
                service.reload()
                if service.attrs.get('UpdateStatus') and service.attrs['UpdateStatus'].get('State') == 'updating':
                    self.logger.info('Service {} is in status `updating`. Waiting 1s...'.format(service.name))
                    pause.seconds(1)
                else:
                    updating = False
            if service.attrs.get('PreviousSpec'):
                current_image = service.attrs['PreviousSpec']['TaskTemplate']['ContainerSpec']['Image']
                previous_image = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
                if current_image == previous_image:
                    self.logger.info('No updates for service {}'.format(service.name))
                else:
                    self.logger.warning('Service {} has been updated'.format(service.name))
                    prometheus.PROM_SVC_UPDATE_COUNTER.labels(service.name, service.id, service.short_id).inc(1)

    def logging(self):
        """ Configures the logging """
        self.logger = logging.getLogger(__name__)
        loglevel = os.environ.get('LOGLEVEL', 'WARNING')
        gelf_enabled = False
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
                _ix_id=os.path.splitext(sys.modules['__main__'].__file__)[0][1:],
            )
            self.logger.addHandler(GELF)
            gelf_enabled = True
            self.logger.warning('LOGLEVEL="{}"'.format(loglevel))
            self.logger.warning('Initialized logging with GELF enabled: {}'.format(gelf_enabled))

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
