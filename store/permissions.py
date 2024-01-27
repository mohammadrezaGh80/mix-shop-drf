from rest_framework import permissions

from .models import Seller


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
