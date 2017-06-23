# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
class Contact(models.Model):
    user_id = models.CharField(max_length=255)
    access_hash = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    owner = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

class User(models.Model):
    phone = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    user_id = models.CharField(max_length=255)
    access_hash = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)
