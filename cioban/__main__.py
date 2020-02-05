#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" A docker swarm service for automatically updating your services to the latest image tag push. """

import os
import sys
from . import cioban
from .lib import log as logging
from .lib import constants

log = logging.setup_logger(
    name='cioban',
    level=os.environ.get('LOGLEVEL', 'INFO'),
    gelf_host=os.environ.get('GELF_HOST'),
    gelf_port=int(os.environ.get('GELF_PORT', 12201)),
    _ix_id=os.environ.get(os.path.splitext(sys.modules['__main__'].__file__)[0]),
)

if __name__ == '__main__':
    options = {'notifiers': [], 'blacklist': []}

    if os.environ.get('FILTER_SERVICES'):
        filters = os.environ.get('FILTER_SERVICES')
        filters = filters.split('=', 1)
        options['filters'] = {filters[0]: filters[1]}
        log.info(f"FILTER_SERVICES: '{options['filters']}'")

    if os.environ.get('BLACKLIST_SERVICES'):
        blacklist = os.environ.get('BLACKLIST_SERVICES')
        options['blacklist'] = blacklist.split(' ')
        log.info(f"BLACKLIST_SERVICES: '{options['blacklist']}'")

    if os.environ.get('TELEGRAM_TOKEN'):
        options['telegram_token'] = os.environ.get('TELEGRAM_TOKEN')
        log.info('TELEGRAM_TOKEN is set')

    if os.environ.get('TELEGRAM_CHAT_ID'):
        options['telegram_chat_id'] = os.environ.get('TELEGRAM_CHAT_ID')
        log.info('TELEGRAM_CHAT_ID is set')

    if os.environ.get('GOTIFY_URL'):
        options['gotify_url'] = os.environ.get('GOTIFY_URL')
        log.info(f"GOTIFY_URL: {options['gotify_url']}")

    if os.environ.get('GOTIFY_TOKEN'):
        options['gotify_token'] = os.environ.get('GOTIFY_TOKEN')
        log.info(f"GOTIFY_TOKEN is set")

    if os.environ.get('NOTIFY_INCLUDE_NEW_IMAGE'):
        options['notify_include_new_image'] = True
        log.info('NOTIFY_INCLUDE_NEW_IMAGE is set')

    if os.environ.get('NOTIFY_INCLUDE_OLD_IMAGE'):
        options['notify_include_old_image'] = True
        log.info('NOTIFY_INCLUDE_OLD_IMAGE is set')

    if options.get('telegram_token') and options.get('telegram_chat_id'):
        options['notifiers'].append('telegram')

    if options.get('gotify_url') and options.get('gotify_token'):
        options['notifiers'].append('gotify')

    options['sleep_time'] = os.environ.get('SLEEP_TIME', '5m')
    log.info(f"SLEEP_TIME: {options['sleep_time']}")

    options['prometheus_port'] = int(os.environ.get('PORT', 9308))
    log.info(f"PORT: {options['prometheus_port']}")

    startup_message = "Starting {} {}-{} with prometheus metrics on port {}".format(
        __package__,
        constants.VERSION,
        constants.BUILD,
        options['prometheus_port'],
    )
    log.warning(startup_message)

    c = cioban.Cioban(**options)
    c.notify(title="CIOBAN Startup", message=startup_message)
    c.run()
