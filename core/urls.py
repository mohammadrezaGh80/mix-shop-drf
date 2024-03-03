from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
router.register('users', views.UserViewSet, basename='user')


urlpatterns = [
    path('refresh/', TokenRefreshView.as_view(), name='refresh-token'),
    path('otp/', views.OTPGenericAPIView.as_view(), name='otp'),
    path('otp/verify/', views.VerifyOTPGenericAPIView.as_view(), name='verify-otp'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('set_password/', views.SetPasswordGenericAPIView.as_view(), name='set-password')
] + router.urls
