#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Constants declarations """

VERSION = None
BUILD = None

# Messages

W001 = (
        'Not using cioban.webhook.auth.token since both cioban.webhook.auth.basic and cioban.webhook.auth.token are'
        ' set. Either coose a different value for cioban.webhook.auth.token.header or don\'t use cioban.auth.basic.'
)
