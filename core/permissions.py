from rest_framework import permissions
from .models import User


class IsAdminUser(permissions.BasePermission):
    """Allows access only to admin users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')


class IsVendorUser(permissions.BasePermission):
    """Allows access only to vendor users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'vendor')


class IsCustomerUser(permissions.BasePermission):
    """Allows access only to customer users."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'customer')


class IsVendorOrAdmin(permissions.BasePermission):
    """Allows access only to vendor users or admin."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'vendor' or request.user.role == 'admin')
        )


class IsCustomerOrAdmin(permissions.BasePermission):
    """Allows access only to customer users or admin."""
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            (request.user.role == 'customer' or request.user.role == 'admin')
        )