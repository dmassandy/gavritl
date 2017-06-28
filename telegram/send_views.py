# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json
from django.shortcuts import render
from django.conf import settings

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .utils import validate_fields,phone_norm,download_file

from .apps import redisClient
from .models import TLUser

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def send_text(request):
    logging.info('send text request')
    required = ['from', 'to', 'body', 'first_name', 'internal_id']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, body, first_name, internal_id"}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_from = phone_norm(request.data['from'])
    phone_to = phone_norm(request.data['to'])

    isExists = TLUser.objects.filter(phone=phone_from,state='authorized').exists()
    if not isExists:
        return Response({"message":"User not authorized. Please sign in/sign up first!"}, status=status.HTTP_400_BAD_REQUEST)
    
    req = {
        'type' : 'send_text',
        'phone_from' : phone_from,
        'phone_to' : phone_to,
        'body' : request.data['body'],
        'first_name' : request.data['first_name'],
        'last_name' : request.data.get('last_name', ''),
        'internal_id' : request.data['internal_id']
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))
    return Response({"message": "Success!"})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def send_media(request):
    required = ['from', 'to', 'url', 'type', 'internal_id']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, url, type, internal_id"}, status=status.HTTP_400_BAD_REQUEST)
    phone_from = phone_norm(request.data['from'])
    phone_to = phone_norm(request.data['to'])

    # check for client has been authorized
    isExists = TLUser.objects.filter(phone=phone_from,state='authorized').exists()
    if not isExists:
        return Response({"message":"User not authorized. Please sign in/sign up first!"}, status=status.HTTP_400_BAD_REQUEST)

    # download media
    (file_name, file_path) = download_file(request.data['url'], settings.TELETHON_USER_MEDIA_DIR)

    req = {
        'type' : 'send_media',
        'phone_from' : phone_from,
        'phone_to' : phone_to,
        'caption' : request.data.get('caption',None),
        'first_name' : request.data['first_name'],
        'last_name' : request.data.get('last_name', ''),
        'media_type' : request.data['type'],
        'file_name' : file_name,
        'file_path' : file_path,
        'internal_id' : request.data['internal_id']
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))
    
    return Response({"message": "Success!"})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def status_read(request):
    required = ['phone_number', 'from', 'max_id']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, from, max_id"}, status=status.HTTP_400_BAD_REQUEST)
    phone_number = phone_norm(request.data['phone_number'])
    phone_from = phone_norm(request.data['from'])
    # check for client has been authorized
    isExists = TLUser.objects.filter(phone=phone_number,state='authorized').exists()
    if not isExists:
        return Response({"message":"User not authorized. Please sign in/sign up first!"}, status=status.HTTP_400_BAD_REQUEST)

    req = {
        'type' : 'status_read',
        'phone_from' : phone_from,
        'phone_number' : phone_number,
        'max_id' : request.data['max_id']
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))

    return Response({"message": "Success!"})