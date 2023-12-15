from rest_framework import permissions


class IsCustomAdminUser(permissions.BasePermission):

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        return bool(
            request.method in ['GET', 'HEAD', 'OPTIONS', 'DELETE']
            or request.user
            and request.user.is_staff
            and request.user == obj
        )
