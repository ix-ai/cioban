#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" notification core """

import logging
import importlib

log = logging.getLogger('cioban')


def start():
    """ Returns an instance of Register() """
    return CoreNotifiers()


def key_to_title(key=""):
    """ converts a configuration key in form 'a_is_b' to a title in form 'A Is B' """
    parsed = ""
    keys = key.split('_')
    for k in keys:
        parsed += '{} '.format(k.capitalize())
    return parsed[:-1]


class CoreNotifiers():
    """ the notification core class """

    notifiers = [
        'telegram',
    ]

    registered = []

    def register(self, notifier, **kwargs):
        """ registers a notifier """
        log.debug(f'Registering {notifier}')
        for n in self.notifiers:
            if n == notifier:
                instance = importlib.import_module(f'cioban.notifiers.{notifier}_notifier')
                self.registered.append({notifier: instance.Notifier(**kwargs)})
                log.debug(f'Registered {notifier}')

    def notify(self, **kwargs):
        """ dispatches a notification to the registered notifiers """
        for i in self.registered:
            for notifier in i:
                log.debug(f'Sending notification to {notifier}')
                i[notifier].notify(**kwargs)
