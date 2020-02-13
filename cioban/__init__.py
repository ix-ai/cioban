#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from .lib import log as logging
from .lib import constants

version = f'{constants.VERSION}-{constants.BUILD}'
log = logging.setup_logger(
    name='cioban',
    level=os.environ.get('LOGLEVEL', 'INFO'),
    gelf_host=os.environ.get('GELF_HOST'),
    gelf_port=int(os.environ.get('GELF_PORT', 12201)),
    _ix_id=__package__,
    _version=version,
)
