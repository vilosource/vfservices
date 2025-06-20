"""
Views for Identity Admin app
"""
import logging
from django.views.generic import View, TemplateView
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.utils.decorators import method_decorator

from .decorators import identity_admin_required, identity_admin_api_required
from .api_client import IdentityAdminAPIClient
from .exceptions import APIError, NotFoundError
from .constants import ROLE_PROFILES, DEFAULT_PAGE_SIZE

logger = logging.getLogger(__name__)


class IdentityAdminBaseView(View):
    """Base view with common functionality for identity admin views."""
    
    @method_decorator(identity_admin_required)
    def dispatch(self, request, *args, **kwargs):
        """Initialize API client and handle common errors."""
        # Get JWT token from cookies
        jwt_token = request.COOKIES.get('jwt') or request.COOKIES.get('jwt_token')
        if not jwt_token:
            messages.error(request, "Authentication token not found. Please log in again.")
            return redirect(f"{settings.EXTERNAL_SERVICE_URLS['identity']}/login/?next={request.build_absolute_uri()}")
        
        # Initialize API client
        try:
            self.api_client = IdentityAdminAPIClient(
                jwt_token=jwt_token,
                base_url=getattr(settings, 'IDENTITY_PROVIDER_URL', None)
            )
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            messages.error(request, "Failed to connect to Identity Provider service.")
            return redirect(f"{settings.EXTERNAL_SERVICE_URLS['identity']}/login/?next={request.build_absolute_uri()}")
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_api_error(self, error: APIError, request):
        """Handle API errors with user-friendly messages."""
        logger.error(f"API Error: {error}")
        
        if hasattr(error, 'status_code'):
            if error.status_code == 401:
                messages.error(request, "Your session has expired. Please log in again.")
                return redirect(f"{settings.EXTERNAL_SERVICE_URLS['identity']}/login/?next={request.build_absolute_uri()}")
            elif error.status_code == 403:
                messages.error(request, "You don't have permission to perform this action.")
            elif error.status_code == 404:
                messages.error(request, "The requested resource was not found.")
            elif error.status_code >= 500:
                messages.error(request, "The server encountered an error. Please try again later.")
            else:
                messages.error(request, str(error))
        else:
            messages.error(request, "An unexpected error occurred. Please try again.")
        
        return None


@method_decorator(identity_admin_required, name='dispatch')
class DashboardView(TemplateView):
    """Main dashboard view."""
    template_name = 'identity_admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Identity Administration'
        context['identity_provider_url'] = settings.EXTERNAL_SERVICE_URLS.get('identity', 'https://identity.vfservices.viloforge.com')
        return context


@method_decorator(identity_admin_required, name='dispatch')
class UserListView(TemplateView):
    """List users with search and pagination."""
    template_name = 'identity_admin/user_list.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'User Management'
        context['identity_provider_url'] = settings.EXTERNAL_SERVICE_URLS.get('identity', 'https://identity.vfservices.viloforge.com')
        return context


@method_decorator(identity_admin_required, name='dispatch')
class UserDetailView(TemplateView):
    """View user details including roles and attributes."""
    template_name = 'identity_admin/user_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'User Details'
        context['user_id'] = self.kwargs.get('user_id')
        context['identity_provider_url'] = settings.EXTERNAL_SERVICE_URLS.get('identity', 'https://identity.vfservices.viloforge.com')
        return context


class UserCreateView(IdentityAdminBaseView):
    """Create new user."""
    
    def get(self, request):
        context = {
            'page_title': 'Create User',
            'role_profiles': ROLE_PROFILES,
        }
        return render(request, 'identity_admin/users/create.html', context)
    
    def post(self, request):
        # TODO: Implement user creation
        messages.success(request, "User created successfully.")
        return redirect(reverse('identity_admin:user_list'))


@method_decorator(identity_admin_required, name='dispatch')
class UserEditView(TemplateView):
    """Edit user details."""
    template_name = 'identity_admin/user_edit.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit User'
        context['user_id'] = self.kwargs.get('user_id')
        context['identity_provider_url'] = settings.EXTERNAL_SERVICE_URLS.get('identity', 'https://identity.vfservices.viloforge.com')
        return context


@method_decorator(identity_admin_required, name='dispatch')
class UserRolesView(TemplateView):
    """Manage user roles."""
    template_name = 'identity_admin/user_roles.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Manage Roles'
        context['user_id'] = self.kwargs.get('user_id')
        context['identity_provider_url'] = settings.EXTERNAL_SERVICE_URLS.get('identity', 'https://identity.vfservices.viloforge.com')
        return context


class RoleListView(IdentityAdminBaseView):
    """List all available roles."""
    
    def get(self, request):
        try:
            services = self.api_client.list_services()
            roles = self.api_client.list_roles()
            
            # Group roles by service
            roles_by_service = {}
            for role in roles:
                service_name = role.get('service_name')
                if service_name not in roles_by_service:
                    roles_by_service[service_name] = []
                roles_by_service[service_name].append(role)
            
            context = {
                'page_title': 'Role Browser',
                'services': services,
                'roles_by_service': roles_by_service,
            }
            
            return render(request, 'identity_admin/roles/list.html', context)
            
        except APIError as e:
            self.handle_api_error(e, request)
            return render(request, 'identity_admin/roles/list.html', {
                'page_title': 'Role Browser',
                'error': str(e)
            })


class RoleAssignView(IdentityAdminBaseView):
    """Assign roles to users."""
    
    def get(self, request):
        context = {
            'page_title': 'Assign Roles',
            'role_profiles': ROLE_PROFILES,
        }
        return render(request, 'identity_admin/roles/assign.html', context)


class ServiceListView(IdentityAdminBaseView):
    """List all services."""
    
    def get(self, request):
        try:
            services = self.api_client.list_services()
            
            context = {
                'page_title': 'Service Registry',
                'services': services,
            }
            
            return render(request, 'identity_admin/services/list.html', context)
            
        except APIError as e:
            self.handle_api_error(e, request)
            return render(request, 'identity_admin/services/list.html', {
                'page_title': 'Service Registry',
                'error': str(e)
            })


# API Views for AJAX

class UserRolesAPIView(IdentityAdminBaseView):
    """API endpoint for managing user roles via AJAX."""
    
    @method_decorator(identity_admin_api_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, user_id):
        """Assign role to user."""
        # TODO: Implement role assignment
        return JsonResponse({'status': 'success'})
    
    def delete(self, request, user_id):
        """Revoke role from user."""
        # TODO: Implement role revocation
        return JsonResponse({'status': 'success'})


class UserAttributesAPIView(IdentityAdminBaseView):
    """API endpoint for managing user attributes via AJAX."""
    
    @method_decorator(identity_admin_api_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, user_id):
        """Get user attributes."""
        try:
            attributes = self.api_client.get_user_attributes(user_id)
            return JsonResponse({'attributes': attributes})
        except APIError as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def post(self, request, user_id):
        """Update user attributes."""
        # TODO: Implement attribute update
        return JsonResponse({'status': 'success'})