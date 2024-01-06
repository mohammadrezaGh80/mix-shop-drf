from rest_framework import permissions

from .models import Seller


class IsCustomerOrSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        seller_queryset = Seller.objects.filter(user_id=request.user.id)

        return bool(
            request.user and request.user.is_authenticated and
            (not seller_queryset.exists() or request.method in permissions.SAFE_METHODS)
        )
    
class IsSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        seller_queryset = Seller.objects.filter(user_id=request.user.id, status=Seller.SELLER_STATUS_ACCEPTED)

        return bool(
            request.user and request.user.is_authenticated and
            seller_queryset.exists() 
        )


class IsAdminUserOrReadOnly(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(
            request.method in permissions.SAFE_METHODS or
            request.user and request.user.is_authenticated and
            request.user.is_staff 
        )
