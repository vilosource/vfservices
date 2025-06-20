"""
URL configuration for azure_costs app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health, name='health'),
    path('debug-auth', views.debug_auth, name='debug-auth'),
    path('debug-middleware', views.debug_middleware, name='debug-middleware'),
    path('private', views.private, name='private'),
    path('test-rbac', views.test_rbac, name='test-rbac'),
]