from django.http import JsonResponse

from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes

from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, UntypedToken
from rest_framework import status
import datetime
from django.contrib.auth.hashers import check_password
from .serializer import RegistrationSerializers
from .serializer import LoginSerializer
from .serializer import UserInfoSerializer
from django.contrib.auth.models import User
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.hashers import make_password
from rest_framework.utils import json


@api_view(['POST'])
@permission_classes([])
def tokenObtainPair(request):
    try:

        login_serializer = LoginSerializer(data=request.data)

        if login_serializer.is_valid():
            email = login_serializer.validated_data.get('email')
            password = login_serializer.validated_data.get('password')
            if "@" in email:
                user_instance = User.objects.get(email=email)
            else:
                user_instance = User.objects.get(username=email)
            if check_password(password, user_instance.password):
                refresh = RefreshToken.for_user(user_instance)

                # return Response({
                #
                #     'access_token': str(refresh.access_token),
                #     'refresh_token': str(refresh),
                #     'token_type': str(refresh.payload['token_type']),
                #     'expiry': refresh.payload['exp'],
                #     'user_id': refresh.payload['user_id'],
                #     'user_object': UserInfoSerializer(user_instance).data,
                #
                #

                return Response({
                    'code': status.HTTP_200_OK,
                    'access_token': str(refresh.access_token),
                    'refresh_token': str(refresh),
                    'token_type': str(refresh.payload['token_type']),
                    'expiry': refresh.payload['exp'],
                    'user_id': refresh.payload['user_id'],
                    'user_object': UserInfoSerializer(user_instance).data,

                })
            else:
                return Response({
                    "code": status.HTTP_401_UNAUTHORIZED,
                    "message": "No active account found with the given credentials",
                    "status_code": 401,
                    "errors": [
                        {
                            "status_code": 401,
                            "message": "No active account found with the given credentials"
                        }
                    ]
                })
        else:
            return Response({
                "code": status.HTTP_401_UNAUTHORIZED,
                "message": "No active account found with the given credentials",
                "status_code": 401,
                "errors": [
                    {
                        "status_code": 401,
                        "message": "Either Email or Password or both not given"
                    }
                ]})
    except Exception as e:
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


@api_view(['POST'])
def tokenRefresh(request):
    try:

        refresh = RefreshToken(token=request.data.get('refresh_token'), verify=True)

        return Response({
            'code': status.HTTP_200_OK,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'token_type': str(refresh.payload['token_type']),
            'expiry': refresh.payload['exp'],
            'user_id': refresh.payload['user_id'],
            'user_object': UserInfoSerializer(User.objects.get(id=refresh.payload['user_id'])).data,

        })
    except Exception as e:
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


@api_view(['POST'])
def tokenVerify(request):
    try:

        verify = UntypedToken(token=request.data.get('access_token'))

        return Response({
            'code':status.HTTP_200_OK,
            'access_token': str(verify.token),
            'token_type': str(verify.payload['token_type']),
            'expiry': verify.payload['exp'],
            'user_id': verify.payload['user_id'],
        })
    except Exception as e:
        return Response({
            "code": status.HTTP_401_UNAUTHORIZED,
            "message": str(e),
            "status_code": 401,
            "errors": [
                {
                    "status_code": 401,
                    "message": str(e)
                }
            ]
        })


# @api_view(['POST'])
# def test_view(request):
#     return Response({
#         "hello": 'hello'
#     }, 200)
    
@api_view(['POST'])
def test_view(request):
    ip_address = request.META.get('HTTP_X_REAL_IP') or \
                 request.META.get('HTTP_X_FORWARDED_FOR') or \
                 request.META.get('REMOTE_ADDR')
    return Response({
        "hello": 'hello',
        "client_ip": ip_address
    }, 200)


# Create your views here.
@api_view(['POST'])
def registration_view(request):
    if request.method == 'POST':
       
        serializer = RegistrationSerializers(data=request.data)


        if serializer.is_valid():
            serializer.save()
        
            return Response({
                'code': status.HTTP_200_OK,
                'response': "successfully registered user",
                'data': serializer.data
                
                
            })
        else:
            return Response({
                'code':status.HTTP_400_BAD_REQUEST,
                'message': "Error Occured",
                'error':serializer.errors
            })
