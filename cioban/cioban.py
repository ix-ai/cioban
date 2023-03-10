#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A docker swarm service for automatically updating your services to the latest image tag push. """

import logging
from datetime import datetime
import requests
import pause
import docker
from prometheus_client import start_http_server
from cronsim import CronSim, CronSimError
from .lib import constants
from .lib import prometheus
from .lib import notifiers
from .lib.webhooks import Webhooks

log = logging.getLogger('cioban')


class Cioban():
    """ The main class """
    settings = {
        'filter_services': {},
        'blacklist_services': {},
        'sleep_time': '6h',
        'schedule_time': False,
        'prometheus_port': 9308,
        'notifiers': [],
        'notify_include_image': False,
        'notify_include_new_image': False,
        'notify_include_old_image': False,
    }
    docker = docker.from_env()
    notifiers = notifiers.start()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.settings:
                self.settings[k] = v
            else:
                log.debug(f'{k} not found in settings. Ignoring.')
        prometheus.PROM_INFO.info({'version': f'{constants.VERSION}-{constants.BUILD}'})

        # Test schedule_time
        if self.settings['schedule_time']:
            log.debug('Disabling SLEEP_TIME because SCHEDULE_TIME is set.')
            try:
                CronSim(self.settings['schedule_time'], datetime.now())
            except (CronSimError) as e:
                raise CronSimError(f"{self.settings['schedule_time']} not understood. The error: {e}") from CronSimError

        relation = {
            's': 'seconds',
            'm': 'minutes',
            'h': 'hours',
            'd': 'days',
            'w': 'weeks',
        }

        try:
            self.sleep = int(self.settings['sleep_time'])
            self.sleep_type = 'minutes'
        except ValueError as exc:
            try:
                self.sleep = int(self.settings['sleep_time'][:-1])
            except ValueError as e:
                raise ValueError(f"{self.settings['sleep_time']} not understood. The error: {e}") from e

            if self.settings['sleep_time'][-1] in relation:
                self.sleep_type = relation[self.settings['sleep_time'][-1]]
            else:
                raise ValueError(f"{self.settings['sleep_time']} not understood") from exc

        self.register_notifiers(**kwargs)

        log.debug('Cioban initialized')

    def register_notifiers(self, **kwargs):
        """
        checks in self.settings['notifiers'] for all the to be registered notifiers then look at all kwargs for any keys
        beginning with the notifier name. It then registeres the notifier with the options for it.
        """
        if self.settings.get('notifiers'):
            for notifier in self.settings['notifiers']:
                notifier_options = {}
                for k, v in kwargs.items():
                    if k.lower().startswith(notifier.lower()):
                        notifier_options.update({k.lower(): v})
                self.notifiers.register(notifier, **notifier_options)

    def get_port(self) -> int:
        """ returns the configured prometheus port from self.settings['prometheus_port'] """
        return self.settings['prometheus_port']

    def run(self):
        """ prepares the run and then triggers it. this is the actual loop """
        start_http_server(self.settings['prometheus_port'])  # starts the prometheus metrics server
        log.info(f"Listening on port {self.settings['prometheus_port']}")
        while True:
            self.__set_timer()
            log.info(f'Sleeping for {self.sleep} {self.sleep_type}')
            prometheus.PROM_STATE_ENUM.state('sleeping')
            wait = getattr(pause, self.sleep_type)
            wait(self.sleep)
            prometheus.PROM_STATE_ENUM.state('running')
            log.info('Starting update run')
            self._run()

    def __set_timer(self):
        self.sleep_type = 'seconds'
        cron_timer = CronSim(self.settings['schedule_time'], datetime.now())
        self.sleep = (next(cron_timer) - datetime.now()).seconds + 1
        log.debug(f"Based on the cron schedule '{self.settings['schedule_time']}', next run is in {self.sleep}s")

    def __get_updated_image(self, image, image_sha):
        """ checks if an image has an update """
        registry_data = None
        updated_image = None
        try:
            registry_data = self.docker.images.get_registry_data(image)
        except (docker.errors.APIError, requests.exceptions.ReadTimeout) as error:
            log.error(f'Failed to retrieve the registry data for {image}. The error: {error}')

        if registry_data:
            digest = registry_data.attrs['Descriptor']['digest']
            updated_image = f'{image}@{digest}'

            if image_sha == digest:
                updated_image = False
                log.debug(f'{image}@{image_sha}: No update available')

        return updated_image

    def __get_image_parts(self, image_with_digest):
        image_parts = image_with_digest.split('@', 1)
        image = image_parts[0]
        image_sha = None

        # if there's no sha in the image name, restart the service **with** sha
        try:
            image_sha = image_parts[1]
        except IndexError:
            pass

        return image, image_sha

    def __update_image(self, service, update_image):
        service_name = service.name
        log.info(f'Updating service {service_name} with image {update_image}')
        service_updated = False
        try:
            service.update(image=update_image, force_update=True)
            service_updated = True
        except docker.errors.APIError as error:
            log.error(f'Failed to update {service_name}. The error: {error}')
        else:
            log.warning(f'Service {service_name} has been updated')
        return service_updated

    @prometheus.PROM_UPDATE_SUMMARY.time()
    def _run(self):
        """ the actual run """
        services = []
        try:
            services = self.get_services()
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            log.error('Cannot connect to docker')

        for service in services:
            webhook = Webhooks(service)
            try:
                service_name = service.name
                image_with_digest = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
                image, image_sha = self.__get_image_parts(image_with_digest)
                prometheus.PROM_SVC_UPDATE_COUNTER.labels(service_name, service.id, service.short_id, image).inc(0)
                update_image = self.__get_updated_image(image_sha=image_sha, image=image)
                service_updated = False
                if update_image:
                    service_updated = self.__update_image(service, update_image)

                if service_updated:
                    webhook.trigger()
                    updating = True
                    while updating:
                        service.reload()
                        service_updated = True

                        if (
                                service.attrs.get('UpdateStatus')
                                and service.attrs['UpdateStatus'].get('State') == 'updating'
                        ):
                            log.debug(f'Service {service_name} is in status `updating`. Waiting 1s...')
                            pause.seconds(1)
                        else:
                            log.debug(f'Service {service_name} has converged.')
                            updating = False

                if service_updated:
                    prometheus.PROM_SVC_UPDATE_COUNTER.labels(service_name, service.id, service.short_id, image).inc(1)
                    notify = {
                        'service_name': service_name,
                        'service_short_id': service.short_id,
                    }
                    if self.settings['notify_include_image']:
                        notify['image'] = image
                    if self.settings['notify_include_old_image']:
                        notify['old_image'] = image_with_digest
                    if self.settings['notify_include_new_image']:
                        notify['new_image'] = service.attrs['Spec']['TaskTemplate']['ContainerSpec']['Image']
                    self.notify(**notify)
            except docker.errors.NotFound as error:
                log.debug(f'Exception caught: {error}')
                log.warning(f'Service {service_name} disappeared. Reloading the service list.')
                services = self.get_services()

    def get_services(self):
        """ gets the list of services and filters out the black listed """
        services = self.docker.services.list(filters=self.settings['filter_services'])
        for blacklist_service in self.settings['blacklist_services']:
            for service in services:
                if service.name == blacklist_service:
                    log.debug(f'Blacklisted {blacklist_service}')
                    services.remove(service)
        return services

    def notify(self, **kwargs):
        """ Sends a notification through the registered notifiers """
        self.notifiers.notify(**kwargs)
