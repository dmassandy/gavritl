# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

@api_view()
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def hello_world(request):
    return Response({"message": "Hello, world!"})