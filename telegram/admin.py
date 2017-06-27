# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import TLContact, TLUser

admin.site.register(TLContact)
admin.site.register(TLUser)
