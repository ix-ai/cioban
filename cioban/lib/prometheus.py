#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Initializes the prometheus metrics """

from prometheus_client import Summary, Counter, Info, Enum

# Prometheus metrics
PROM_UPDATE_SUMMARY = Summary('update_run_seconds', 'Time spent processing updates')
PROM_SVC_UPDATE_COUNTER = Counter(
    'service_updated', 'Shows if a service has been updated', [
        'name',
        'id',
        'short_id',
        'image'
    ]
)
PROM_INFO = Info('cioban', 'Information about cioban')
PROM_STATE_ENUM = Enum('cioban_state', 'The current state of cioban', states=['running', 'sleeping'])
