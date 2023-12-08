from django.urls import path

from . import views


urlpatterns = [
    path('otp/', views.OTPGenericAPIView.as_view(), name='otp'),
    path('otp/verify/', views.VerifyOTPGenericAPIView.as_view(), name='verify-otp'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('set_password/', views.SetPasswordGenericAPIView.as_view(), name='set-password')
]
