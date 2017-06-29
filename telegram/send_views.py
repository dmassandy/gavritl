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

available_media_types = ['image', 'video', 'audio', 'document', 'location', 'url', 'contact']
downloadable_media_types = ['image', 'video', 'audio', 'document']

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
    required = ['from', 'to', 'type', 'internal_id', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, type, internal_id, 'first_name"}, status=status.HTTP_400_BAD_REQUEST)
    phone_from = phone_norm(request.data['from'])
    phone_to = phone_norm(request.data['to'])

    # check for client has been authorized
    isExists = TLUser.objects.filter(phone=phone_from,state='authorized').exists()
    if not isExists:
        return Response({"message":"User not authorized. Please sign in/sign up first!"}, status=status.HTTP_400_BAD_REQUEST)

    if request.data['type'] not in available_media_types:
        return Response({"message":"Unknown media type {}".format(request.data['type'])}, status=status.HTTP_400_BAD_REQUEST)

    req = {}
    if request.data['type'] in downloadable_media_types:
        media_required_fields = ['url']
        if not validate_fields(request.data, media_required_fields):
            return Response({"message":"Invalid params request, required for media type : url"}, status=status.HTTP_400_BAD_REQUEST)
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
    elif request.data['type'] == "contact":
        contact_required_fields = ['contact_phone_number', 'contact_first_name']
        if not validate_fields(request.data, contact_required_fields):
            return Response({"message":"Invalid params request, required for contact type : contact_phone_number, contact_first_name"}, status=status.HTTP_400_BAD_REQUEST)
        req = {
            'type' : 'send_media',
            'phone_from' : phone_from,
            'phone_to' : phone_to,
            'first_name' : request.data['first_name'],
            'last_name' : request.data.get('last_name', ''),
            'media_type' : request.data['type'],
            'internal_id' : request.data['internal_id'],
            'contact_phone_number' : request.data.get('contact_phone_number', ''),
            'contact_first_name' : request.data.get('contact_first_name', ''),
            'contact_last_name' : request.data.get('contact_last_name', '')
        }
    elif request.data['type'] == "location":
        location_required_fields = ['lat', 'long']
        if not validate_fields(request.data, location_required_fields):
            return Response({"message":"Invalid params request, required for location type : lat, long"}, status=status.HTTP_400_BAD_REQUEST)
        
        # try parse lat/long to float
        lat = request.data['lat']
        try:
            lat = float(lat)
        except ValueError as ve :
            return Response({"message":"Invalid lat value type!"}, status=status.HTTP_400_BAD_REQUEST)
        
        long = request.data['long']
        try:
            long = float(long)
        except ValueError as ve :
            return Response({"message":"Invalid long value type!"}, status=status.HTTP_400_BAD_REQUEST)
        
        req = {
            'type' : 'send_media',
            'phone_from' : phone_from,
            'phone_to' : phone_to,
            'first_name' : request.data['first_name'],
            'last_name' : request.data.get('last_name', ''),
            'media_type' : request.data['type'],
            'internal_id' : request.data['internal_id'],
            'lat' : lat,
            'long' : long,
            'title' : request.data.get('title'),
            'address' : request.data.get('address'),
            'provider' : request.data.get('provider'),
            'venue_id' : request.data.get('venue_id')
        }
    elif request.data['type'] == "url":
        url_required_fields = ['url']
        if not validate_fields(request.data, url_required_fields):
            return Response({"message":"Invalid params request, required for location type : lat, long"}, status=status.HTTP_400_BAD_REQUEST)
        req = {
            'type' : 'send_media',
            'phone_from' : phone_from,
            'phone_to' : phone_to,
            'first_name' : request.data['first_name'],
            'last_name' : request.data.get('last_name', ''),
            'media_type' : request.data['type'],
            'internal_id' : request.data['internal_id'],
            'url' : request.data['url']
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