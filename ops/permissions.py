"""
Custom permissions for ops app - JobOps system.
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class for admin-only access.
    Only users with 'admin' role can access.
    """

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                request.user.role == 'admin'
        )

class CanManageUsers(permissions.BasePermission):
    """
    Only admins can create/edit users.
    All authenticated users can view users.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (
                request.user and
                request.user.is_authenticated and
                request.user.role == 'admin'
        )

class IsAdminOrSalesAgent(permissions.BasePermission):
    """
    Permission class for admin or sales agent.
    Used for job creation and management.
    """

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                request.user.role in ['admin', 'sales_agent']
        )


class IsTechnician(permissions.BasePermission):
    """
    Permission class for technician-only access.
    """

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                request.user.role == 'technician'
        )

class CanCreateJob(permissions.BasePermission):
    """
    Only admins and sales agents can create jobs.
    All authenticated users can view jobs.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        if request.method == 'POST' and (view is None or view.action == 'create'):
            return (
                    request.user and
                    request.user.is_authenticated and
                    request.user.role in ['admin', 'sales_agent']
            )

        return request.user and request.user.is_authenticated


class CanUpdateJobProgress(permissions.BasePermission):
    """
    Only assigned technicians can update job progress.
    Admins have full access.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated"""
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions"""

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.role == 'admin':
            return True

        if hasattr(obj, 'assigned_to'):
            if request.user.role == 'technician':
                return obj.assigned_to == request.user

            if request.user.role == 'sales_agent':
                return obj.created_by == request.user

        if hasattr(obj, 'job'):
            if request.user.role == 'technician':
                return obj.job.assigned_to == request.user

            if request.user.role == 'sales_agent':
                return obj.job.created_by == request.user

        return False


class CanManageEquipment(permissions.BasePermission):
    """
    All authenticated users can view equipment.
    Only admins can create/update/delete equipment.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated

        return (
                request.user and
                request.user.is_authenticated and
                request.user.role == 'admin'
        )


class CanViewAnalytics(permissions.BasePermission):
    """
    Only admins can view analytics.
    """

    def has_permission(self, request, view):
        return (
                request.user and
                request.user.is_authenticated and
                request.user.role == 'admin'
        )