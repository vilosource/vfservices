from django.urls import path
from . import views

app_name = 'demo'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('rbac/', views.rbac_dashboard, name='rbac_dashboard'),
    path('api-explorer/', views.api_explorer, name='api_explorer'),
    path('permissions/', views.permission_matrix, name='permission_matrix'),
    path('playground/', views.playground, name='playground'),
    
    # API endpoints for demo functionality
    path('api/switch-user/', views.switch_demo_user, name='switch_demo_user'),
    path('api/test-endpoint/', views.test_api_endpoint, name='test_api_endpoint'),
    path('api/user-permissions/', views.get_user_permissions, name='get_user_permissions'),
]