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
router.register('list-waiting-comments', views.CommentListWaitingViewSet, basename='list-waiting-comments')
router.register('carts', views.CartViewSet, basename='cart')
router.register('orders', views.OrderViewSet, basename='order')

customers_router = routers.NestedDefaultRouter(router, 'customers', lookup='customer')
customers_router.register('addresses', views.AddressCustomerViewSet, basename='customer-addresses')

sellers_router = routers.NestedDefaultRouter(router, 'sellers', lookup='seller')
sellers_router.register('addresses', views.AddressSellerViewSet, basename='seller-addresses')
sellers_router.register('products', views.SellerMeProductViewSet, basename='seller-products')

seller_products_router = routers.NestedDefaultRouter(sellers_router, 'products', lookup='product')
seller_products_router.register('images', views.ProductImageViewSet, basename='seller-product-images')

products_router = routers.NestedDefaultRouter(router, 'products', lookup='product')
products_router.register('comments', views.CommentViewSet, basename='product-comments')
products_router.register('images', views.ProductImageViewSet, basename='product-images')

carts_router = routers.NestedDefaultRouter(router, 'carts', lookup='cart')
carts_router.register('items', views.CartItemViewset, basename='cart-items')

urlpatterns = [
    path('request-seller/', views.RequestSellerGenericAPIView.as_view(), name='seller-request'),
    path('products/<int:product_pk>/comments/<int:comment_pk>/like/', views.CommentLikeAPIView.as_view(), name='comment-like'),
    path('products/<int:product_pk>/comments/<int:comment_pk>/dislike/', views.CommentDisLikeAPIView.as_view(), name='comment-dislike'),
    path('orders/me/', views.OrderMeViewSet.as_view({'get': 'list'}), name='order-me'),
    path('orders/me/<int:pk>/', views.OrderMeViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='order-me-detail')
] + router.urls + customers_router.urls + sellers_router.urls + products_router.urls + seller_products_router.urls + carts_router.urls
