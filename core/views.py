from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import status, generics
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAdminUser

from .serializers import OTPSerializer, VerifyOTPSerializer, CustomTokenObtainPairSerializer, \
                          SetPasswordSerializer, UserSerializer, UserCreateSerializer
from .models import OTP
from .throttles import RequestOTPThrottle
from .paginations import CustomLimitOffsetPagination
from store.models import Seller

User = get_user_model()


class OTPGenericAPIView(generics.GenericAPIView):
    serializer_class = OTPSerializer

    def get_throttles(self):
        if self.request.method == "POST":
            return [RequestOTPThrottle()]
        return []

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True) 
        otp_obj = serializer.save()

        # for connect to Kavenegar SMS service
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
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated_data = serializer.validated_data
            phone = validated_data.get('phone')
            password = validated_data.get('password')
            request_id = validated_data.get('id')

            try:
                otp_obj = OTP.objects.get(
                    id=request_id,
                    phone=phone,
                    password=password,
                    expired_datetime__gte=timezone.now(),
                )

                try:
                    user = User.objects.get(phone=phone)
                except User.DoesNotExist:
                    user = User(phone=phone)
                    user.set_unusable_password()
                    user.save()
                
                otp_obj.delete()

                refresh_token = RefreshToken.for_user(user=user)
                return Response({
                        'refresh': str(refresh_token),
                        'access': str(refresh_token.access_token), 
                        'user_id': user.id,
                        'phone': user.phone,
                    }, status=status.HTTP_200_OK)
            
            except OTP.DoesNotExist:
                return Response({'detail': _('Your one-time password is incorrect or has expired!')}, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class SetPasswordGenericAPIView(generics.GenericAPIView):
    serializer_class = SetPasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = self.serializer_class(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': _('Your password has been successfully changed.')}, status=status.HTTP_200_OK)


class UserViewSet(ModelViewSet):
    http_method_names = ['get', 'head', 'options', 'post', 'put', 'delete']
    queryset = User.objects.all().order_by('-id')
    permission_classes = [IsAdminUser]  
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if getattr(instance, 'seller', False) and instance.seller.status == Seller.SELLER_STATUS_ACCEPTED and instance.seller.products.count() > 0:
            return Response({'detail': _('There is some products relating this seller, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)
        elif (getattr(instance, 'seller', False) and instance.seller.status != Seller.SELLER_STATUS_ACCEPTED) or not getattr(instance, 'seller', False):
            if instance.customer.orders.count() > 0: # TODO: just orders that status is unpaind
                return Response({'detail': _('There is some orders relating this customer, Please remove them first.')}, status=status.HTTP_400_BAD_REQUEST)

        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET', 'PUT'], permission_classes=[IsAuthenticated])
    def me(self, request, *args, **kwargs):
        user = request.user
        if request.method == 'GET':
            serializer = UserSerializer(user)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = UserSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)