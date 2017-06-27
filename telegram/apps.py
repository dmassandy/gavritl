# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.apps import AppConfig
from django.conf import settings

gavriTLManager = None

class TelegramConfig(AppConfig):
    name = 'telegram'
    verbose_name = 'Gavri Telegram API'
    def ready(self):
        from .tl_manager import GavriTLManager
        global gavriTLManager
        logging.info('Executing initialization code')
        gavriTLManager = GavriTLManager(settings.TELEGRAM_API_ID, settings.TELEGRAM_API_HASH, session_base_path=settings.TELETHON_SESSIONS_DIR)

