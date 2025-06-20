"""
URL configuration for admin API endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .admin_views import (
    UserViewSet, ServiceViewSet, RoleViewSet,
    BulkOperationsView, AuditLogView
)

# Create router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='admin-user')
router.register(r'services', ServiceViewSet, basename='admin-service')
router.register(r'roles', RoleViewSet, basename='admin-role')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('bulk/assign-roles/', BulkOperationsView.as_view(), name='admin-bulk-assign-roles'),
    path('audit-log/', AuditLogView.as_view(), name='admin-audit-log'),
]