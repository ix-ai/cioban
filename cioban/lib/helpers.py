#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Helper functions """

import logging
import os
# pylint: disable=deprecated-module
from distutils.util import strtobool

log = logging.getLogger("cioban")


def gather_environ(keys=None) -> dict:
    """
    Return a dict of environment variables correlating to the keys dict
    :param keys: The environ keys to use, each of them correlating to `int`, `list`, `string`, `boolean` or `filter`
    :return: A dict of found environ values
    """
    if not keys:
        keys = {
            'filter_services': 'filter',
            'blacklist_services': 'list',
            'telegram_token': 'string',
            'telegram_chat_id': 'string',
            'gotify_url': 'string',
            'gotify_token': 'string',
            'gotify_default_priority': 'int',
            'notify_include_image': 'boolean',
            'notify_include_new_image': 'boolean',
            'notify_include_old_image': 'boolean',
            'schedule_time': 'string',
            'sleep_time': 'string',
            'prometheus_port': 'int',
        }
    environs = {}
    for key, key_type in keys.items():
        if os.environ.get(key.upper()):
            environs.update({key: os.environ[key.upper()]})
            if key_type == 'int':
                try:
                    environs[key] = int(environs[key])
                except ValueError:
                    log.warning(f"`{environs[key]}` not understood for {key.upper()}. Ignoring.")
                    del environs[key]
                    continue
            if key_type == 'list':
                environs[key] = environs[key].split(' ')
            if key_type == 'boolean':
                try:
                    environs[key] = bool(strtobool(environs[key]))
                except ValueError:
                    log.warning(f"`{environs[key]}` not understood for {key.upper()}. Setting to False.")
                    environs[key] = False
                    continue
            if key_type == 'filter':
                filters = environs[key].split('=', 1)
                environs[key] = {filters[0]: filters[1]}
            log.info(f'{key.upper()} is set')
    return environs


def short_msg(msg: str, chars=150) -> str:
    """ Truncates the message to {chars} characters and adds three dots at the end """
    return (str(msg)[:chars] + '..') if len(str(msg)) > chars else str(msg)
