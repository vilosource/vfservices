from django.urls import path
from . import views

app_name = 'identity_admin'

urlpatterns = [
    # Main dashboard (replaces /admin)
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # User Management
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:user_id>/', views.UserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/edit/', views.UserEditView.as_view(), name='user_edit'),
    path('users/<int:user_id>/roles/', views.UserRolesView.as_view(), name='user_roles'),
    
    # Role Management
    path('roles/', views.RoleListView.as_view(), name='role_list'),
    path('roles/assign/', views.RoleAssignView.as_view(), name='role_assign'),
    
    # Service Registry
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    
    # API Endpoints (for AJAX)
    path('api/users/<int:user_id>/roles/', views.UserRolesAPIView.as_view(), name='api_user_roles'),
    path('api/users/<int:user_id>/attributes/', views.UserAttributesAPIView.as_view(), name='api_user_attributes'),
]