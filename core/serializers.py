from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from .models import OTP

User = get_user_model()


class OTPSerializer(serializers.ModelSerializer):
    request_id = serializers.CharField(source='id', read_only=True)

    class Meta:
        model = OTP
        fields = ['request_id', 'phone']
        extra_kwargs = {
            'phone': {'write_only': True}
        }

    def create(self, validated_data):
        otp = OTP()
        otp.phone = validated_data.get('phone')
        otp.generate_password()
        otp.save()
        return otp


class VerifyOTPSerializer(serializers.ModelSerializer):
    request_id = serializers.UUIDField(source='id')

    class Meta:
        model = OTP
        fields = ['request_id', 'phone', 'password']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field].label = 'username'

    def validate(self, attrs):
        data = super().validate(attrs)

        data['user_id'] = self.user.pk
        data['phone'] = self.user.phone
        data['email'] = self.user.email
        
        return data

class SetPasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        max_length=128,
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = ['password']

    def validate(self, attrs):
        password = attrs.get('password', None)
        validate_password(password)
        return attrs
    
    def update(self, instance, validated_data):
        password = validated_data.get('password')
        instance.set_password(password)
        instance.save()
        return instance
    

class UserSerializer(serializers.ModelSerializer):
    has_password = serializers.BooleanField(source='password', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'phone', 'email', 'has_password']
        read_only_fields = ['phone']


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'phone', 'email']
