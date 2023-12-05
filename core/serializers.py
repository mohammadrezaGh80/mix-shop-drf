from rest_framework import serializers

from .models import OTP


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
    request_id = serializers.CharField(source='id')

    class Meta:
        model = OTP
        fields = ['request_id', 'phone', 'password']
