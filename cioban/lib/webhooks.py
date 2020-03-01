#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Handles webhooks """
import logging
from urllib.parse import urlparse
import requests
from docker.client import DockerClient
from . import constants
from .helpers import short_msg

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
        'auth.basic.password': {
            'default': None,
        },
        'auth.token.header': {
            'default': 'Authorization',
        },
        'auth.token.type': {
            'default': 'token',
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
        if self.labels.get('http.url'):
            self.active = True
            log.debug(f'{self.service.name}: Webhook active')

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

            if label == 'http.url' and not self.validate_url(value):
                log.warning(f"{self.service.name}: Value '{value}' for label {label} is invalid")
            else:
                log.debug(f"{self.service.name}: Using '{value}' for {label}")
                result = {label: value}
                self.labels.update(result)

        return result

    def trigger(self):
        """ Triggers the webhook """
        if not self.active:
            log.debug(f"{self.service.name}: Webhook not configured")
            return

        url = self.labels['http.url']
        method = self.labels.get('http.method', self.describe_labels['http.method']['default'])
        timeout = int(self.labels.get('http.timeout', self.describe_labels['http.timeout']['default']))
        auth = None
        headers = {
            'User-Agent': f'cioban {constants.VERSION}-{constants.BUILD}'
        }

        if self.labels.get('auth.basic.username') and self.labels.get('auth.basic.password'):
            auth = (self.labels['auth.basic.username'], self.labels['auth.basic.password'])
            if self.labels.get('auth.token.token') and (
                    not self.labels.get('auth.token.header')
                    or self.labels.get('auth.token.header') == 'Authorization'
            ):
                log.warning(f"{self.service.name}: {constants.W001} (W001)")

        if self.labels.get('auth.token.token'):
            auth_name = self.labels.get('auth.token.header', self.describe_labels['auth.token.header']['default'])
            auth_value = self.labels.get('auth.token.type', self.describe_labels['auth.token.type']['default'])
            headers.update({
                auth_name: f"{auth_value} {self.labels['auth.token.token']}"
            })
        action = getattr(requests, method)

        try:
            response = action(url, auth=auth, headers=headers, timeout=timeout)
            log.debug(f"{self.service.name}: Webhook response: {response.content}")
        except requests.exceptions.RequestException as e:  # this catches all exceptions from requests
            log.warning(f"{self.service.name}: Could not trigger webhook. The Exception: {short_msg(e)}")
            log.debug(f"{self.service.name}: The Exception: {e}")
