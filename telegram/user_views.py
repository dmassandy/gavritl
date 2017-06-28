# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import logging
from time import sleep
import json
from django.shortcuts import render
from django.conf import settings

# Create your views here.
from rest_framework import status
from rest_framework.decorators import api_view,authentication_classes,permission_classes
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .utils import validate_fields,phone_norm,phone_number_only,str2bool

from .apps import redisClient

from .models import TLUser

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def request_code(request):
    required = ['phone_number','first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number_norm = phone_norm(request.data['phone_number'])

    isReplace = request.data.get('force', 'False')
    req = {
        'type' : 'request_code',
        'phone_number' : phone_number_norm,
        'first_name' : request.data['first_name'],
        'last_name' : request.data.get('last_name', ''),
        'force' : str2bool(isReplace)
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))

    return Response({"message": "Success!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def sign_in(request):
    required = ['phone_number', 'code', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, code, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number_norm = phone_norm(request.data['phone_number'])

    isExistsAndRequestCodeSent = TLUser.objects.filter(phone=phone_number_norm,state='request-code sent').exists()
    if not isExistsAndRequestCodeSent:
        return Response({"message":"Please send request code first!"}, status=status.HTTP_400_BAD_REQUEST)
    
    req = {
        'type' : 'sign_in',
        'phone_number' : phone_number_norm,
        'first_name' : request.data['first_name'],
        'last_name' : request.data.get('last_name', ''),
        'code' : request.data['code'],
        'pw' : request.data.get('pw', None)
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))

    return Response({"message": "Success!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def sign_up(request):
    required = ['phone_number', 'code', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, code, first_name"}, status=status.HTTP_400_BAD_REQUEST)
    
    phone_number_norm = phone_norm(request.data['phone_number'])

    isExistsAndRequestCodeSent = TLUser.objects.filter(phone=phone_number_norm,state='request-code sent').exists()
    if not isExistsAndRequestCodeSent:
        return Response({"message":"Please send request code first!"}, status=status.HTTP_400_BAD_REQUEST)
    
    req = {
        'type' : 'sign_up',
        'phone_number' : phone_number_norm,
        'first_name' : request.data['first_name'],
        'last_name' : request.data.get('last_name', ''),
        'code' : request.data['code']
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))

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
    
    phone_number_norm = phone_norm(request.data['phone_number'])

    isExists = TLUser.objects.filter(phone=phone_number_norm,state='authorized').exists()
    if not isExists:
        return Response({"message":"User not authorized. Please sign in/sign up first!"}, status=status.HTTP_400_BAD_REQUEST)
    
    req = {
        'type' : 'set_presence',
        'phone_number' : phone_number_norm,
        'presence' : request.data['presence']
    }
    
    redisClient.publish(settings.REDIS_OUTGOING_JOB_QUEUE, json.dumps(req))

    return Response({"message": "Success!"})