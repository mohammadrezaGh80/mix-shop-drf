from rest_framework.response import Response
from rest_framework import status, generics
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.db import transaction

from .serializers import OTPSerializer, VerifyOTPSerializer
from .models import OTP
from .throttles import RequestOTPThrottle

User = get_user_model()


class OTPGenericAPIView(generics.GenericAPIView):
    serializer_class = OTPSerializer

    def get_throttles(self):
        if self.request.method == "POST":
            return [RequestOTPThrottle()]
        return []

    def get_serializer_class(self):
        return super().get_serializer_class()

    def post(self, request, *args, **kwargs):
        serializer = OTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) 
        otp_obj = serializer.save()

        # try:
        #     api = KavenegarAPI(settings.SMS_API_KEY)
        #     params = {
        #         'receptor': otp_obj.phone,
        #         'template': settings.OTP_TEMPLATE,
        #         'token': otp_obj.password,
        #     }   
        #     response = api.verify_lookup(params)
        #     print(response)
        # except APIException as e: 
        #     print(e)
        # except HTTPException as e: 
        #     print(e)

        return Response(serializer.data, status=status.HTTP_200_OK)


class VerifyOTPGenericAPIView(generics.GenericAPIView):
    serializer_class = VerifyOTPSerializer

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            serializer = VerifyOTPSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            phone = validated_data.get('phone')
            password = validated_data.get('password')

            otp_queryset = OTP.objects.filter(
                id=validated_data.get('id'),
                phone=phone,
                password=password,
                expired_datetime__gte=timezone.now(),
            )

            if otp_queryset.exists():
                user, created = User.objects.get_or_create(phone=phone)
                if created:
                    user.is_active = True
                    user.save()

                refresh_token = RefreshToken.for_user(user=user)
                return Response({
                        'access': str(refresh_token.access_token), 
                        'refresh': str(refresh_token)
                    }, status=status.HTTP_200_OK)
            return Response({'detail': 'Your one-time password is incorrect or has expired!'}, status=status.HTTP_400_BAD_REQUEST)
