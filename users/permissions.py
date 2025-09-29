from rest_framework import permissions


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
