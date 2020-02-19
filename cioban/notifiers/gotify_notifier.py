#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Gotify """

import logging
from urllib.parse import urljoin
import requests
from . import core

log = logging.getLogger('cioban')


def start(**kwargs):
    """ Returns an instance of the GotifyNotifier """
    return GotifyNotifier(**kwargs)


class GotifyNotifier(core.Notifier):
    """ The GotifyNotifier class """

    def __init__(self, **kwargs):
        self.token = kwargs['gotify_token']
        self.url = urljoin(kwargs['gotify_url'], f'/message?token={self.token}')
        log.debug(f"Initialized with {kwargs['gotify_url']}")
        super().__init__()

    def post_message(self, title, message):
        """ sends a notification to gotify """
        resp = None
        try:
            resp = requests.post(self.url, json={
                'title': title,
                'message': message,
                'extras': {'client::display': {'contentType': 'text/markdown'}}
            })
        except requests.exceptions.RequestException as e:
            # Print exception if reqeuest fails
            log.error(f'Could not connect to Gotify server. The error: {e}')

        if resp:
            # Print request result if server returns http error code
            if resp.status_code is not requests.codes.ok:  # pylint: disable=no-member
                log.error(f'{bytes.decode(resp.content)}')
            else:
                log.info("Sent message to gotify")
                log.debug(f"Message: {message}")

    def notify(self, title="", **kwargs):
        """ parses the arguments, formats the message and dispatches it """
        log.debug('Sending message to gotify')
        message = ""
        if kwargs.get('message'):
            message = kwargs['message']
        else:
            for k, v in kwargs.items():
                message += f'**{core.key_to_title(k)}**: `{v}`  \n'
        self.post_message(title, message)
