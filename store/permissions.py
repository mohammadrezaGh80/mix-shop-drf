from rest_framework import permissions
from django.shortcuts import get_object_or_404
from django.http import Http404

from .models import Seller, Product


class IsCustomerOrSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_authenticated and
            not getattr(request.user, 'seller', False)
        )
    
class IsSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            getattr(request.user, 'seller', False) and 
            request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED
        )


class IsAdminUserOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_authenticated and
            request.user.is_staff 
        )


class IsAdminUserOrSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff or
            getattr(request.user, 'seller', False) and 
            request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED
        )


class IsAdminUserOrSellerOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff or
            getattr(request.user, 'seller', False) and 
            request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED and
            request.user.seller == obj.seller
        )


class IsAdminUserOrCommentOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff or
            request.user and request.user.is_authenticated and
            getattr(request.user, 'seller', request.user.customer) == obj.content_object
        )
    

class IsCommentOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        return bool(
            request.user and request.user.is_authenticated and
            getattr(request.user, 'seller', request.user.customer) == obj.content_object
        )
    

class ProductImagePermission(permissions.BasePermission):
    product = None

    def has_permission(self, request, view):
        try:
            product_pk = int(view.kwargs.get('product_pk'))
        except ValueError:
            raise Http404

        if (not ProductImagePermission.product) or \
        (ProductImagePermission.product and ProductImagePermission.product.pk != product_pk):
            ProductImagePermission.product = get_object_or_404(Product, pk=product_pk)
        
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff or
            getattr(request.user, 'seller', False) and 
            request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED and
            request.user.seller == ProductImagePermission.product.seller
        )
