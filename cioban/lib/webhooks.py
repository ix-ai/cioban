#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Handles webhooks """
import logging
from docker.client import DockerClient
from urllib.parse import urlparse

log = logging.getLogger('cioban')


class Webhooks():
    """ The Webhooks class definition"""

    describe_labels = {
        'http.url': {
            'default': None,
        },
        'http.method': {
            'default': 'post',
            'values': ['get', 'post'],
        },
        'http.timeout': {
            'default': 2,
        },
        'auth.basic.username': {
            'default': None,
        },
        'auth.basic.passwork': {
            'default': None,
        },
        'auth.token.header': {
            'default': None,
        },
        'auth.token.type': {
            'default': None,
        },
        'auth.token.token': {
            'default': None,
        },
    }

    def __init__(self, service: DockerClient.services):
        self.service = service
        self.labels = {}
        self.active = False
        self.gather_labels(service)

    def gather_labels(self, service):
        """ gathers the webhooks for the service """
        for label in self.describe_labels:
            value = service.attrs['Spec']['Labels'].get(f"cioban.webhook.{label}")
            if value:
                self._update_label(label, value)
        if self.active:
            log.debug(f'{self.service.name}: Webhook registered')

    def validate_url(self, url: str) -> bool:
        """ Validates if a string is a valid URL """
        try:
            result = urlparse(url)
            if result.scheme in ['http', 'https']:
                return True
        except ValueError:
            pass

        return False

    def _update_label(self, label: str, value: str):
        """ updates a label to a value based on self.describe_labels """
        result = False
        label_definition = self.describe_labels.get(label)
        if label_definition:
            if label_definition.get('values'):
                if value not in label_definition['values']:
                    log.warning(
                        f"{self.service.name}: Value '{value}' for label {label} is invalid."
                        f" Using '{label_definition['default']}'."
                    )
                    value = label_definition['default']

            log.debug(f"{self.service.name}: Registering {label}: {value}")
            result = {label: value}
            self.labels.update(result)

        return result

    def trigger(self):
        """ Triggers the webhook """
        if not self.active:
            log.debug("No webhook configured")
            return

        url = self.labels['http.url']
        method = self.labels.get('http.method', self.describe_labels['http.method']['default'])
        timeout = int(self.labels.get('http.timeout', self.describe_labels['http.timeout']['default']))
        log.debug(f"{self.service.name}: {url} {method} {timeout}")
