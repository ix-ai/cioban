#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Telegram """

import logging
import time
import telegram
from . import core

log = logging.getLogger('cioban')


class Notifier():
    """ The notify class """

    def __init__(self, **kwargs):
        self.chat_id = kwargs['telegram_chat_id']
        self.notifier = telegram.Bot(token=kwargs['telegram_token'])
        log.debug('Initialized')

    def __post_message(self, message):
        """ sends the notification to telegram """
        retry = True
        while retry is True:
            try:
                self.notifier.sendMessage(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=True,
                )
                log.info("Sent message to telegram.")
                log.debug(f"Message: {message}")
                retry = False
            except (TimeoutError, telegram.error.TimedOut, telegram.error.RetryAfter) as error:
                try:
                    retry_after = 0.5 + int(error.retry_after)
                except AttributeError:
                    retry_after = 2
                log.warning(f'Exception caught - retrying in {retry_after}s: {error}')
                time.sleep(retry_after)
            except (telegram.error.Unauthorized) as error:
                exit_message = f'{error} - check TELEGRAM_TOKEN - skipping retries.'
                log.error(exit_message)
                # Fake message_sent and return
                retry = False
            except (telegram.error.BadRequest) as error:
                exit_message = str(error)
                if str(error) == 'Chat not found':
                    exit_message = f'{exit_message} - check TELEGRAM_CHAT_ID'
                exit_message = f'{exit_message} - skipping retries. The exception: {error}'
                log.error(exit_message)
                retry = False
            except Exception as error:
                log.error(f"Failed to send message! Exception: {error}")
                retry = False

    def notify(self, title="", **kwargs):
        """ parses the arguments, formats the message and dispatches it """
        log.debug('Sending notification to telegram')
        message = f'<b>{title}</b>\n'
        if kwargs.get('message'):
            message += kwargs['message']
        else:
            for k, v in kwargs.items():
                message += f'{core.key_to_title(k)}: {v}\n'
        self.__post_message(message)

    def noop(self):
        """ Does nothing """
