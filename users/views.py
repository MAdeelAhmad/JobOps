from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from users.models import User
from users.serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer
)
from users.permissions import CanManageUsers


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User management.

    Only admins can create/update/delete users.
    All authenticated users can view users.
    """

    queryset = User.objects.all()
    permission_classes = [CanManageUsers]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'date_joined', 'role']
    ordering = ['username']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        """Filter users based on query parameters"""
        queryset = User.objects.all()

        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)

        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')

        return queryset

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
