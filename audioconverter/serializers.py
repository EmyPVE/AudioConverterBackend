from rest_framework import serializers
from .models import Conversionlog, Subscription
from .models import User
from django.contrib.auth.hashers import make_password


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'name', 'description', 'duration_months', 'max_conversions_per_month']

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'created_at', 'subscription', 'start_date', 'end_date']
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True}  # Nu este necesar să fie trimis în request
        }

    def create(self, validated_data):
        user = User(
            username=validated_data['username'],
            email=validated_data['email'],
            created_at=validated_data.get('created_at')
        )
        user.password_hash = make_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.subscription = validated_data.get('subscription', instance.subscription)
        instance.start_date = validated_data.get('start_date', instance.start_date)
        instance.end_date = validated_data.get('end_date', instance.end_date)

        # Update parola dacă este furnizată
        password = validated_data.get('password', None)
        if password is not None:
            instance.password_hash = make_password(password)

        instance.save()
        return instance

class ConversionlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversionlog
        fields = '__all__'