from django.urls import path

from . import views


urlpatterns = [
    path('otp/', views.OTPGenericAPIView.as_view(), name='otp'),
    path('otp/verify/', views.VerifyOTPGenericAPIView.as_view(), name='verify-otp')
]
