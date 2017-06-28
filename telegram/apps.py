# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.apps import AppConfig
from django.conf import settings

import redis

redisClient = None

class TelegramConfig(AppConfig):
    name = 'telegram'
    verbose_name = 'Gavri Telegram API'
    def ready(self):
        global redisClient
        logging.info('Executing initialization code')
        redisClient = redis.StrictRedis(host=settings.REDIS_CLIENT_HOST, port=settings.REDIS_CLIENT_PORT, db=0)
        logging.info('is redisClient None : {}'.format(str(redisClient is None)))
        

