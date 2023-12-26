from rest_framework import permissions

from .models import Seller


class IsCustomerOrSeller(permissions.BasePermission):

    def has_permission(self, request, view):
        seller_queryset = Seller.objects.filter(user_id=request.user.id)

        return bool(
            request.user and request.user.is_authenticated and
            (not seller_queryset.exists() or request.method in permissions.SAFE_METHODS)
        )
