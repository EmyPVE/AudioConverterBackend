# audioconverter/views.py
import io
import json
import os
import uuid
import jwt
import datetime
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate
from dateutil.relativedelta import relativedelta
from rest_framework.request import Request
from django.views.decorators.csrf import csrf_exempt
from rest_framework.parsers import JSONParser
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.views import APIView
from rest_framework import exceptions
import logging
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .models import Conversionlog, Subscription, User

from .serializers import ConversionlogSerializer, SubscriptionSerializer, UserSerializer

from rest_framework.response import Response

from audioconverter.forms import AudioUploadForm
from .utils import convert_audio
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def convert_upload(request):
    if request.method == 'POST':
        form = AudioUploadForm(request.POST, request.FILES)
        if form.is_valid():
            audio_file = form.cleaned_data['audio_file']
            audio_format = request.POST.get('conversion_format', 'mp3')
            print('Received file:', audio_file.name, 'Format:', audio_format)

            file_path = os.path.join(settings.MEDIA_ROOT, 'input', audio_file.name)
            with open(file_path, 'wb') as destination:
                for chunk in audio_file.chunks():
                    destination.write(chunk)

            try:
                converted_file = convert_audio(file_path, audio_format)

                user_id = None

                auth_header = request.META.get('HTTP_AUTHORIZATION')

                if auth_header is not None:
                    parts = auth_header.split()
                    if len(parts) == 2 and parts[1].lower() != 'null':
                        token = parts[1]
                        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
                        user_id = User.objects.get(id=payload.get('user_id'))
                    else:
                        user_id = None
                else:
                    user_id = None

                log = Conversionlog(
                    user=user_id if user_id else None,
                    input_file=audio_file.name,
                    output_file=converted_file,
                    file_size=(os.path.getsize(file_path))/1000000,
                    conversion_timestamp=datetime.datetime.utcnow(),
                )
                log.save()

                return JsonResponse({'success': True, 'converted_file': converted_file})
            except ValueError as ve:
                return JsonResponse({'success': False, 'error': str(ve)})

    return JsonResponse({'detail': 'Invalid request method'}, status=400)



class SubscriptionList(APIView):

    def get(self, request, format=None):
        subscriptions = Subscription.objects.all()
        serializer = SubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data)

class UserList(APIView):

    def post(self, request, format=None):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        try:
            user = User.objects.get(username=username)
            if check_password(password, user.password_hash):
                jti = str(uuid.uuid4())
                payload = {
                    'user_id': user.id,
                    'iss': "https://127.0.0.1:8000",
                    'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1),
                    'nbf': datetime.datetime.utcnow(),
                    'iat': datetime.datetime.utcnow(),
                    'type': "access",
                    'jti': jti
                }
                token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
                return JsonResponse({'token': token}, safe=False)
            else:
                return JsonResponse({'detail': 'Invalid Credentials'}, status=401)
        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'detail': 'Invalid Credentials'}, status=401)
    else:
        return JsonResponse({'detail': 'Invalid request'}, status=400)
        
@csrf_exempt
@require_GET
def user_detail(request):
    auth_header = request.META.get('HTTP_AUTHORIZATION')

    if auth_header is None:
        return JsonResponse({'detail': 'Authorization token not provided'}, status=401)
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return JsonResponse({'detail': 'Authorization header must be Bearer token'}, status=401)
    
    token = parts[1]
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        return JsonResponse({'detail': 'Token expired'}, status=401)
    except jwt.DecodeError:
        return JsonResponse({'detail': 'Error decoding token'}, status=401)

    try:
        user = User.objects.get(id=payload.get('user_id'))
    except User.DoesNotExist:
        return JsonResponse({'detail': 'User not found'}, status=404)

    return JsonResponse({
    'user_id': user.id,
    'username': user.username,
    'subscription': user.subscription.name if user.subscription else None,
    'created_at': user.created_at,
    'end_date': user.end_date
}, status=200)



@csrf_exempt
def change_password(request):
    if request.method == 'PUT':
        try:
            token = request.META.get('HTTP_AUTHORIZATION', None)
            if token is None:
                return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)

            try:
                payload = jwt.decode(token.split(' ')[1], settings.SECRET_KEY, algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return JsonResponse({'detail': 'Token expired'}, status=401)
            except jwt.DecodeError:
                return JsonResponse({'detail': 'Invalid token'}, status=401)

            user_id = payload['user_id']
            user = User.objects.get(id=user_id)

            data = json.loads(request.body)
            old_password = data.get('old_password')
            new_password = data.get('new_password')

            if not check_password(old_password, user.password_hash):
                return JsonResponse({'detail': 'Old password is incorrect'}, status=401)

            user.password_hash = make_password(new_password)
            user.save()

            return JsonResponse({'detail': 'Password changed successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'detail': 'Invalid JSON'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'detail': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'detail': str(e)}, status=500)

    else:
        return JsonResponse({'detail': 'Invalid request method'}, status=400)
    

@csrf_exempt
@require_POST
def update_subscription(request):
    try:
        token = request.META.get('HTTP_AUTHORIZATION', None)
        if token is None:
            return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)

        try:
            payload = jwt.decode(token.split(' ')[1], settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'detail': 'Token expired'}, status=401)
        except jwt.DecodeError:
            return JsonResponse({'detail': 'Invalid token'}, status=401)

        user_id = payload['user_id']
        user = User.objects.get(id=user_id)

        data = json.loads(request.body)
        subscription_id = data.get('subscriptionId')

        user.subscription_id = subscription_id

        sub = Subscription.objects.get(id=subscription_id)
        
        user.start_date = datetime.datetime.now()
        user.end_date = datetime.datetime.now() + relativedelta(months=sub.duration_months)

        user.save()

        return JsonResponse({'message': 'Subscription updated successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'detail': 'Invalid JSON'}, status=400)
    except User.DoesNotExist:
        return JsonResponse({'detail': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=500)
