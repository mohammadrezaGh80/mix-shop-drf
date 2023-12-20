from rest_framework.routers import DefaultRouter

from rest_framework_nested import routers

from . import views


router = DefaultRouter()
router.register('customers', views.CustomerViewSet, basename='customer')

customers_router = routers.NestedDefaultRouter(router, 'customers', lookup='customer')
customers_router.register('addresses', views.AddressViewSet, basename='customer-addresses')

urlpatterns = router.urls + customers_router.urls
