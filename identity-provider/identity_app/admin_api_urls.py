from django.urls import path
from . import admin_api_views

app_name = 'admin_api'

urlpatterns = [
    # User Management
    path('users/', admin_api_views.UserListCreateView.as_view(), name='user-list'),
    path('users/<int:user_id>/', admin_api_views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/set-password/', admin_api_views.SetPasswordView.as_view(), name='set-password'),
    
    # Role Management
    path('users/<int:user_id>/roles/', admin_api_views.UserRolesView.as_view(), name='user-roles'),
    path('users/<int:user_id>/roles/<int:role_id>/', admin_api_views.RevokeRoleView.as_view(), name='revoke-role'),
    
    # Service and Role Listing
    path('services/', admin_api_views.ServiceListView.as_view(), name='service-list'),
    path('roles/', admin_api_views.RoleListView.as_view(), name='role-list'),
]