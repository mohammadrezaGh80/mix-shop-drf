from rest_framework.routers import DefaultRouter
from django.urls import path

from rest_framework_nested import routers

from . import views


router = DefaultRouter()
router.register('customers', views.CustomerViewSet, basename='customer')
router.register('sellers', views.SellerViewSet, basename='seller')
router.register('list-requests', views.SellerListRequestsViewSet, basename='list-requests')
router.register('categories', views.CategoryViewSet, basename='category')
router.register('products', views.ProductViewSet, basename='product')

customers_router = routers.NestedDefaultRouter(router, 'customers', lookup='customer')
customers_router.register('addresses', views.AddressCustomerViewSet, basename='customer-addresses')

sellers_router = routers.NestedDefaultRouter(router, 'sellers', lookup='seller')
sellers_router.register('addresses', views.AddressSellerViewSet, basename='seller-addresses')

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('comments', views.CommentViewSet, basename='product-comments')

urlpatterns = router.urls + customers_router.urls + sellers_router.urls + products_router.urls + [
    path('request-seller/', views.RequestSellerGenericAPIView.as_view(), name='seller-request'),
]
