# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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
def request_code(request):
    required = ['phone_number']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number"}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({"message": "Hello, world!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def sign_in(request):
    required = ['phone_number', 'code']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, code"}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({"message": "Hello, world!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def sign_up(request):
    required = ['phone_number', 'code', 'first_name']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, code, first_name"}, status=status.HTTP_404_NOT_FOUND)

    return Response({"message": "Hello, world!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def log_out(request):
    required = ['phone_number']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": "Hello, world!"})

@api_view(['POST'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def set_presence(request):
    required = ['phone_number', 'presence']
    if not validate_fields(request.data, required):
        return Response({"message":"Invalid params request, required : phone_number, presence"}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({"message": "Hello, world!"})