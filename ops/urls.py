"""
URL configuration for ops app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    EquipmentViewSet,
    JobViewSet,
    JobTaskViewSet,
    TechnicianDashboardView,
    JobAnalyticsView
)

router = DefaultRouter()
router.register(r'equipment', EquipmentViewSet, basename='equipment')
router.register(r'jobs', JobViewSet, basename='job')
router.register(r'tasks', JobTaskViewSet, basename='task')

urlpatterns = [
    path('technician-dashboard/', TechnicianDashboardView.as_view(), name='technician-dashboard'),
    path('analytics/', JobAnalyticsView.as_view(), name='job-analytics'),

    path('', include(router.urls)),
]