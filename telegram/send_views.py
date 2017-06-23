# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.shortcuts import render

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .utils import validate_fields

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def send_text(request):
    logging.info('send text request')
    required = ['from', 'to', 'body']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, body"}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({"message": "Hello, world!"})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def send_media(request):
    required = ['from', 'to', 'url']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, url"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Hello, world!"})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def status_read(request):
    required = ['from', 'to', 'url']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, url"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Hello, world!"})