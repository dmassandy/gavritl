# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
from django.shortcuts import render
from django.conf import settings

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from .utils import validate_fields,phone_norm,download_file

from .apps import gavriTLManager

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def send_text(request):
    logging.info('send text request')
    required = ['from', 'to', 'body', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, body, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_from = phone_norm(request.data['from'])
    phone_to = phone_norm(request.data['to'])

    client = gavriTLManager.get_user(phone_from)
    if client is None:
        return Response({"message":"Client has not been registered.!"}, status=status.HTTP_404_NOT_FOUND)

    message_id = client.send_text_message(phone_to, request.data['body'], request.data['first_name'], last_name=request.data.get('last_name'))
    if message_id is None:
        return Response({"message":"Failed sent message!"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Success!", "message_id" : message_id})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def send_media(request):
    required = ['from', 'to', 'url', 'type']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, url, type"}, status=status.HTTP_400_BAD_REQUEST)
    phone_from = phone_norm(request.data['from'])
    phone_to = phone_norm(request.data['to'])

    client = gavriTLManager.get_user(phone_from)
    if client is None:
        return Response({"message":"Client has not been registered.!"}, status=status.HTTP_404_NOT_FOUND)
    
    # download media
    (file_name, file_path) = download_file(request.data['url'], settings.TELETHON_USER_MEDIA_DIR)

    if request.data['type'] == 'image':
        message_id = client.send_photo(file_path, phone_to, request.data.get('caption'), request.data['first_name'], request.data.get('last_name'))
    else:
        message_id = client.send_document(file_path, phone_to, request.data.get('caption'), request.data['first_name'], request.data.get('last_name'))
    if message_id is None:
        return Response({"message":"Failed sent message!"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Success!", "message_id" : message_id})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def status_read(request):
    required = ['from', 'to', 'max_id']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : from, to, max_id"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "Success!"})