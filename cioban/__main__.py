#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from . import cioban
from .lib import helpers
from .lib import constants

version = f'{constants.VERSION}-{constants.BUILD}'
log = logging.getLogger('cioban')

options = helpers.gather_environ()
options['notifiers'] = []

if options.get('telegram_token') and options.get('telegram_chat_id'):
    options['notifiers'].append('telegram')
if options.get('gotify_url') and options.get('gotify_token'):
    options['notifiers'].append('gotify')

startup_message = (f"Starting **{__package__} {version}**")
log.warning(startup_message)

c = cioban.Cioban(**options)
c.notify(title="Startup", message=startup_message)
c.run()
