# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import logging
from time import sleep
from django.shortcuts import render
from django.conf import settings

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .utils import validate_fields,phone_norm,phone_number_only

from .apps import gavriTLManager

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def request_code(request):
    required = ['phone_number','first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    # TO DO : remove [phone_number].session if exist
    session_user_id = phone_number_only(request.data['phone_number']) + '.session'
    session_filepath = os.path.join(settings.TELETHON_SESSIONS_DIR, session_user_id)
    try:
        os.remove(session_filepath)
    except OSError:
        pass
    
    msg = gavriTLManager.add_user(phone_norm(request.data['phone_number']), 
                                    first_name=request.data.get('first_name'), 
                                    last_name=request.data.get('last_name', None))
    if msg:
        if 'code' in msg:
            return Response({"message": msg})
        else:
            return Response({"message":msg}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Success!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def sign_in(request):
    required = ['phone_number', 'code', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, code, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    client = gavriTLManager.get_user(phone_norm(request.data['phone_number']))
    if client is None:
        return Response({"message":"Client has not been registered. Please send request code!"}, status=status.HTTP_404_NOT_FOUND)
    pw = request.data['pw'] if 'pw' in request.data else None
    result_code = client.do_sign_in(request.data['code'], pw=pw)
    if result_code == 0:
        return Response({"message":"Client failed to sign-in!"}, status=status.HTTP_404_NOT_FOUND)
    
    sleep(0.5)
    # sync contacts
    client = gavriTLManager.get_user(request.data['phone_number'])
    if client:
        client.sync_contacts()

    return Response({"message": "Success!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def sign_up(request):
    required = ['phone_number', 'code', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, code, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    
    client = gavriTLManager.get_user(phone_norm(request.data['phone_number']))
    if client is None:
        return Response({"message":"Failed registration! Please send request code first!"}, status=status.HTTP_404_NOT_FOUND)

    result = client.do_sign_up(request.data['code'], request.data['first_name'], request.data.get('last_name', ''))
    if result is not None:
        return Response({"message":"Client failed to sign-up! Error : " + result}, status=status.HTTP_404_NOT_FOUND)

    return Response({"message": "Success!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def log_out(request):
    required = ['phone_number']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number"}, status=status.HTTP_400_BAD_REQUEST)
    return Response({"message": "Success!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def set_presence(request):
    required = ['phone_number', 'presence']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, presence"}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response({"message": "Success!"})


@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def test_sign_in(request):
    required = ['phone_number','first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    msg = gavriTLManager.add_user(phone_norm(request.data['phone_number']), 
                                    first_name=request.data.get('first_name'), 
                                    last_name=request.data.get('last_name', None))
    if msg:
        return Response({"message":msg}, status=status.HTTP_404_NOT_FOUND)
    sleep(0.5)
    # sync contacts
    client = gavriTLManager.get_user(request.data['phone_number'])
    if client:
        client.sync_contacts()

    return Response({"message": "Success!"})