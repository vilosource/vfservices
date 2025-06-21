"""
Admin API views for Identity Provider.
Provides administrative endpoints for user and role management.
"""
import logging
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import UserRole, Role, Service, UserAttribute
from .permissions import IsIdentityAdmin
from .serializers import (
    UserSerializer, UserDetailSerializer, RoleSerializer, 
    ServiceSerializer, UserRoleSerializer
)

logger = logging.getLogger(__name__)


class UserListCreateView(APIView):
    """List users with pagination and filtering, or create new user."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def get(self, request):
        """List users with search and filters."""
        # Get query parameters
        page_num = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 50))
        search = request.GET.get('search', '')
        is_active = request.GET.get('is_active', '')
        has_role = request.GET.get('has_role', '')
        service = request.GET.get('service', '')
        
        # Build query
        queryset = User.objects.all()
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # Apply is_active filter
        if is_active in ['true', 'false']:
            queryset = queryset.filter(is_active=(is_active == 'true'))
        
        # Apply has_role filter
        if has_role == 'true':
            queryset = queryset.filter(user_roles__isnull=False).distinct()
        elif has_role == 'false':
            queryset = queryset.filter(user_roles__isnull=True)
        
        # Apply service filter
        if service:
            queryset = queryset.filter(
                user_roles__role__service__name=service
            ).distinct()
        
        # Order by username
        queryset = queryset.order_by('username')
        
        # Paginate
        paginator = Paginator(queryset, page_size)
        page = paginator.get_page(page_num)
        
        # Serialize users with basic role info
        users_data = []
        for user in page:
            user_data = UserSerializer(user).data
            # Add role summary
            roles = UserRole.objects.filter(
                user=user,
                role__service__is_active=True
            ).select_related('role', 'role__service')
            
            user_data['roles'] = [
                {
                    'id': ur.id,
                    'name': ur.role.name,
                    'display_name': ur.role.display_name,
                    'service': ur.role.service.name
                }
                for ur in roles
            ]
            users_data.append(user_data)
        
        # Build response
        response_data = {
            'count': paginator.count,
            'next': f"?page={page.next_page_number()}" if page.has_next() else None,
            'previous': f"?page={page.previous_page_number()}" if page.has_previous() else None,
            'results': users_data
        }
        
        return Response(response_data)
    
    def post(self, request):
        """Create new user."""
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Handle initial roles if provided
            initial_roles = request.data.get('initial_roles', [])
            for role_data in initial_roles:
                try:
                    role = Role.objects.get(
                        name=role_data.get('role_name'),
                        service__name=role_data.get('service_name')
                    )
                    UserRole.objects.create(
                        user=user,
                        role=role,
                        granted_by=request.user
                    )
                except Role.DoesNotExist:
                    logger.warning(f"Role not found: {role_data}")
            
            return Response(
                UserDetailSerializer(user).data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    """Get, update, or delete user."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def get(self, request, user_id):
        """Get user details with roles and attributes."""
        user = get_object_or_404(User, id=user_id)
        
        # Get user roles with full details
        roles = UserRole.objects.filter(
            user=user,
            role__service__is_active=True
        ).select_related('role', 'role__service', 'granted_by')
        
        # Get user attributes
        attributes = UserAttribute.objects.filter(user=user)
        
        # Build response
        user_data = UserDetailSerializer(user).data
        user_data['roles'] = [
            {
                'id': ur.id,
                'service': ur.role.service.name,
                'service_display': ur.role.service.display_name,
                'name': ur.role.name,
                'display_name': ur.role.display_name,
                'description': ur.role.description,
                'granted_at': ur.granted_at,
                'granted_by': ur.granted_by.username if ur.granted_by else 'System',
                'expires_at': ur.expires_at
            }
            for ur in roles
        ]
        
        user_data['attributes'] = [
            {
                'id': attr.id,
                'service': attr.service.name if attr.service else None,
                'name': attr.name,
                'value': attr.value,
                'updated_at': attr.updated_at
            }
            for attr in attributes
        ]
        
        return Response(user_data)
    
    def put(self, request, user_id):
        """Update user information."""
        user = get_object_or_404(User, id=user_id)
        
        # Don't allow changing username
        data = request.data.copy()
        data.pop('username', None)
        
        serializer = UserSerializer(user, data=data, partial=True)
        if serializer.is_valid():
            user = serializer.save()
            
            # Handle password change separately
            if 'password' in request.data:
                user.set_password(request.data['password'])
                user.save()
            
            return Response(UserDetailSerializer(user).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, user_id):
        """Deactivate user (soft delete)."""
        user = get_object_or_404(User, id=user_id)
        
        # Don't allow deactivating superusers
        if user.is_superuser:
            return Response(
                {'error': 'Cannot deactivate superuser accounts'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user.is_active = False
        user.save()
        
        return Response({'message': 'User deactivated successfully'})


class SetPasswordView(APIView):
    """Set user password."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def post(self, request, user_id):
        """Set new password for user."""
        user = get_object_or_404(User, id=user_id)
        password = request.data.get('password')
        
        if not password:
            return Response(
                {'error': 'Password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(password) < 8:
            return Response(
                {'error': 'Password must be at least 8 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(password)
        user.save()
        
        # TODO: Send password reset email
        
        return Response({'message': 'Password updated successfully'})


class UserRolesView(APIView):
    """Manage user roles."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def get(self, request, user_id):
        """List user's roles."""
        user = get_object_or_404(User, id=user_id)
        
        roles = UserRole.objects.filter(
            user=user,
            role__service__is_active=True
        ).select_related('role', 'role__service', 'granted_by')
        
        roles_data = [
            {
                'id': ur.id,
                'role_id': ur.role.id,
                'service': ur.role.service.name,
                'service_display': ur.role.service.display_name,
                'name': ur.role.name,
                'display_name': ur.role.display_name,
                'description': ur.role.description,
                'granted_at': ur.granted_at,
                'granted_by': ur.granted_by.username if ur.granted_by else 'System',
                'expires_at': ur.expires_at
            }
            for ur in roles
        ]
        
        return Response(roles_data)
    
    def post(self, request, user_id):
        """Assign role to user."""
        user = get_object_or_404(User, id=user_id)
        
        # Get role
        role_name = request.data.get('role_name')
        service_name = request.data.get('service_name')
        
        if not role_name or not service_name:
            return Response(
                {'error': 'role_name and service_name are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            role = Role.objects.get(
                name=role_name,
                service__name=service_name,
                service__is_active=True
            )
        except Role.DoesNotExist:
            return Response(
                {'error': f'Role {role_name} not found in service {service_name}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if already assigned
        if UserRole.objects.filter(user=user, role=role).exists():
            return Response(
                {'error': 'User already has this role'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create role assignment
        user_role = UserRole.objects.create(
            user=user,
            role=role,
            granted_by=request.user,
            expires_at=request.data.get('expires_at')
        )
        
        # TODO: Log this action
        logger.info(f"User {request.user.username} assigned role {role.name} to {user.username}")
        
        return Response({
            'id': user_role.id,
            'message': f'Role {role.display_name} assigned successfully'
        }, status=status.HTTP_201_CREATED)


class RevokeRoleView(APIView):
    """Revoke role from user."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def delete(self, request, user_id, role_id):
        """Revoke role assignment."""
        user_role = get_object_or_404(
            UserRole,
            id=role_id,
            user_id=user_id
        )
        
        # Store info for logging
        role_name = user_role.role.name
        username = user_role.user.username
        
        user_role.delete()
        
        # TODO: Log this action
        logger.info(f"User {request.user.username} revoked role {role_name} from {username}")
        
        return Response({'message': 'Role revoked successfully'})


class ServiceListView(APIView):
    """List all active services."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def get(self, request):
        """Get all active services."""
        services = Service.objects.filter(is_active=True).order_by('name')
        services_data = ServiceSerializer(services, many=True).data
        
        return Response(services_data)


class RoleListView(APIView):
    """List all available roles."""
    permission_classes = [IsAuthenticated, IsIdentityAdmin]
    
    def get(self, request):
        """Get all roles, optionally filtered."""
        service_filter = request.GET.get('service')
        is_global = request.GET.get('is_global')
        
        queryset = Role.objects.filter(
            service__is_active=True
        ).select_related('service').order_by('service__name', 'name')
        
        if service_filter:
            queryset = queryset.filter(service__name=service_filter)
        
        if is_global in ['true', 'false']:
            queryset = queryset.filter(is_global=(is_global == 'true'))
        
        roles_data = []
        for role in queryset:
            role_data = RoleSerializer(role).data
            role_data['service_name'] = role.service.name
            role_data['service_display'] = role.service.display_name
            roles_data.append(role_data)
        
        return Response(roles_data)