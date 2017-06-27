# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class TLContact(models.Model):
    user_id = models.CharField(max_length=255)
    access_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    phone = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

# state : authorized, request-code sent, unauthorized
class TLUser(models.Model):
    phone = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True)
    username = models.CharField(max_length=255, null=True)
    user_id = models.CharField(max_length=255, null=True)
    access_hash = models.CharField(max_length=255, null=True)
    state = models.CharField(max_length=255, default='none')
    isConnected = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
