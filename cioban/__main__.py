#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" processes the environment variables and starts cioban """

import logging
from . import cioban
from .lib import helpers
from .lib import constants

version = f'{constants.VERSION}-{constants.BUILD}'
log = logging.getLogger('cioban')

options = helpers.gather_environ()
options['notifiers'] = []

if options.get('gotify_url') and options.get('gotify_token'):
    options['notifiers'].append('gotify')

c = cioban.Cioban(**options)

startup_message = f"Starting **{__package__} {version}**. Exposing metrics on port {c.get_port()}"
log.warning(startup_message)
c.notify(title="Startup", message=startup_message)

c.run()
