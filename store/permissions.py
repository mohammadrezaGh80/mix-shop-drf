from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.utils.translation import gettext as _

from .models import Seller, Product


class IsCustomerOrSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.user and not request.user.is_authenticated:
            return False
        elif getattr(request.user, 'seller', False) and request.user.seller.status == Seller.SELLER_STATUS_WAITING:
            raise PermissionDenied(detail=_('Your request is under review.'))
        elif getattr(request.user, 'seller', False) and request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED:
            raise PermissionDenied(detail=_('You are currently a seller.'))
        return True
    
    
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
        user = request.user.seller if getattr(request.user, 'seller', False) and request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED \
                                   else request.user.customer
        print(obj.content_object)
        return bool(
            request.user and request.user.is_authenticated and
            request.user.is_staff or
            request.user and request.user.is_authenticated and
            user == obj.content_object
        )
    

class IsCommentOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        user = request.user.seller if getattr(request.user, 'seller', False) and request.user.seller.status == Seller.SELLER_STATUS_ACCEPTED \
                                   else request.user.customer
        return bool(
            request.user and request.user.is_authenticated and
            user == obj.content_object
        )
    

class ProductImagePermission(permissions.BasePermission):
    product = None

    def has_permission(self, request, view):
        try:
            product_pk = int(view.kwargs.get('product_pk'))
        except (ValueError, TypeError):
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
