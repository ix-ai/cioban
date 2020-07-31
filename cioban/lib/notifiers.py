#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" notification core """

import logging
from ix_notifiers.core import IxNotifiers

log = logging.getLogger('cioban')


def start():
    """ Returns an instance of Notify() """
    return Notify()


class Notify(IxNotifiers):
    """ the notification core class """

    def notify(self, **kwargs):
        """ dispatches a notification to the registered notifiers """
        title = kwargs.get('title', 'Service Updated')
        kwargs['title'] = f'CIOBAN: {title}'
        for notifier_name, notifier in self.registered.items():
            log.debug(f'Sending notification to {notifier_name}')
            notification_method = self.__getattribute__(f'{notifier_name}_notify')
            notification_method(notifier=notifier, **kwargs)

    def gotify_notify(self, notifier, **kwargs):
        """ parses the arguments, formats the message and dispatches it """
        log.debug('Sending message to gotify')
        message = ""
        try:
            message = kwargs['message']
        except KeyError:
            for k, v in kwargs.items():
                if k == 'title':
                    break
                message += f'**{notifier.key_to_title(k)}**: `{v}`  \n'
        params = {
            'title': kwargs.get('title', ''),
            'message': message,
        }
        notifier.send(**params)

    def telegram_notify(self, notifier, **kwargs):
        """ parses the arguments, formats the message and dispatches it """
        log.debug('Sending notification to telegram')
        message = f"*{kwargs.get('title')}*\n"
        if kwargs.get('message'):
            message += kwargs['message']
        else:
            for k, v in kwargs.items():
                if k == 'title':
                    break
                message += f"*{notifier.key_to_title(k)}*: `{v}`  \n"
        notifier.send(message=message)

    def null_notify(self, notifier, **kwargs):
        """ dispatches directly """
        notifier.send(f'{kwargs}')
