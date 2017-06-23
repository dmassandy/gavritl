# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.apps import AppConfig

class TelegramConfig(AppConfig):
    name = 'telegram'
    def ready(self):
        logging.info('Executing initialization code')
