from rest_framework.routers import DefaultRouter
from django.urls import path

from rest_framework_nested import routers

from . import views


router = DefaultRouter()
router.register('customers', views.CustomerViewSet, basename='customer')

customers_router = routers.NestedDefaultRouter(router, 'customers', lookup='customer')
customers_router.register('addresses', views.AddressViewSet, basename='customer-addresses')

urlpatterns = router.urls + customers_router.urls + [
    path('request-seller/', views.RequestSellerGenericAPIView.as_view(), name='seller-request')
]
