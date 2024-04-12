from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, PasswordField
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext as _

from .models import OTP
from store.models import Seller

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
    request_id = serializers.UUIDField(source='id', label=_('Request id'))

    class Meta:
        model = OTP
        fields = ['request_id', 'phone', 'password']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'username'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField(write_only=True, label=_('Username'))
        self.fields['password'] = PasswordField(label=_('Password'))

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
        style={'input_type': 'password'},
        label=_('Password')
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
        instance.save(update_fields=['password'])
        return instance
    

class UserSerializer(serializers.ModelSerializer):
    has_password = serializers.BooleanField(source='password', read_only=True)
    email = serializers.EmailField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone', 'email', 'role', 'has_password']
        read_only_fields = ['phone']
    
    def validate_email(self, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        else:
            raise serializers.ValidationError(
                _("This email is already chosen, please enter another email.")
            )
        
    def get_role(self, user):
        if user.is_staff:
            return 'admin'
        elif getattr(user, 'seller', False) and user.seller.status == Seller.SELLER_STATUS_ACCEPTED:
            return 'seller'
        return 'customer'


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'phone', 'email']
