"""
Admin API views for user and role management
"""
import logging
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import BaseAuthentication

from .models import Role, UserRole, Service, ServiceManifest
from .serializers import (
    UserListSerializer, UserDetailSerializer, UserCreateSerializer,
    UserUpdateSerializer, UserRoleSerializer, AssignRoleSerializer,
    SetPasswordSerializer, ServiceSerializer, RoleSerializer,
    BulkAssignRoleSerializer, AuditLogSerializer
)
from .permissions import IsIdentityAdmin
from .services import RBACService, RedisService
from .audit import audit_log

logger = logging.getLogger(__name__)


def get_django_user(request):
    """Get Django User instance from request"""
    if hasattr(request.user, 'id') and request.user.id:
        try:
            return User.objects.get(id=request.user.id)
        except User.DoesNotExist:
            pass
    return None


class JWTCookieAuthentication(BaseAuthentication):
    """
    Custom authentication class that uses JWT from cookies
    but doesn't trigger CSRF checks like SessionAuthentication
    """
    def authenticate(self, request):
        # The JWT middleware has already authenticated the user
        # Check the underlying WSGIRequest, not the DRF request wrapper
        if hasattr(request._request, 'user') and request._request.user.is_authenticated:
            return (request._request.user, None)
        return None


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserViewSet(ModelViewSet):
    """
    Admin API for user management
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsIdentityAdmin]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'date_joined', 'last_login', 'is_active']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        # Filter by role
        has_role = self.request.query_params.get('has_role')
        if has_role:
            queryset = queryset.filter(
                user_roles__role__name=has_role,
                user_roles__expires_at__isnull=True
            ) | queryset.filter(
                user_roles__role__name=has_role,
                user_roles__expires_at__gt=timezone.now()
            )
            queryset = queryset.distinct()
        
        # Filter by service
        service = self.request.query_params.get('service')
        if service:
            queryset = queryset.filter(
                user_roles__role__service__name=service,
                user_roles__expires_at__isnull=True
            ) | queryset.filter(
                user_roles__role__service__name=service,
                user_roles__expires_at__gt=timezone.now()
            )
            queryset = queryset.distinct()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        else:
            return UserDetailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Audit log
            audit_log(
                user=request.user,
                action='user_created',
                resource_type='user',
                resource_id=user.id,
                changes={
                    'username': user.username,
                    'email': user.email,
                    'roles': [r['role_name'] for r in request.data.get('initial_roles', [])]
                },
                request=request
            )
            
            # Clear cache for new user
            RedisService.invalidate_user_cache(user.id)
            
        headers = self.get_success_headers(serializer.data)
        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Track changes for audit
        changes = {}
        for field, value in serializer.validated_data.items():
            old_value = getattr(instance, field)
            if old_value != value:
                changes[field] = {'old': old_value, 'new': value}
        
        with transaction.atomic():
            self.perform_update(serializer)
            
            if changes:
                audit_log(
                    user=request.user,
                    action='user_updated',
                    resource_type='user',
                    resource_id=instance.id,
                    changes=changes,
                    request=request
                )
                
                # Clear cache
                RedisService.invalidate_user_cache(instance.id)
        
        return Response(UserDetailSerializer(instance).data)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Don't allow deleting superusers
        if instance.is_superuser:
            return Response(
                {"error": "Cannot delete superuser accounts"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Soft delete - just deactivate
            instance.is_active = False
            instance.save()
            
            audit_log(
                user=request.user,
                action='user_deactivated',
                resource_type='user',
                resource_id=instance.id,
                changes={'username': instance.username},
                request=request
            )
            
            # Clear cache and sessions
            RedisService.invalidate_user_cache(instance.id)
            # TODO: Clear user sessions
        
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """Set user password"""
        user = self.get_object()
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.set_password(serializer.validated_data['password'])
        user.save()
        
        audit_log(
            user=request.user,
            action='password_changed',
            resource_type='user',
            resource_id=user.id,
            changes={
                'username': user.username,
                'force_change': serializer.validated_data.get('force_change', False)
            },
            request=request
        )
        
        return Response({"status": "Password set successfully"})
    
    @action(detail=True, methods=['get'])
    def roles(self, request, pk=None):
        """List user's roles"""
        user = self.get_object()
        roles = UserRole.objects.filter(
            user=user
        ).select_related('role__service', 'granted_by').order_by('-granted_at')
        
        serializer = UserRoleSerializer(roles, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        """Assign role to user"""
        user = self.get_object()
        serializer = AssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        role = serializer.validated_data['role']
        
        # Check if role already assigned
        existing = UserRole.objects.filter(
            user=user,
            role=role
        ).exclude(
            expires_at__lt=timezone.now()
        ).first()
        
        if existing:
            return Response(
                {"error": "Role already assigned to user"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            django_user = get_django_user(request)
            if not django_user:
                return Response(
                    {"error": "Unable to identify current user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user_role = UserRole.objects.create(
                user=user,
                role=role,
                granted_by=django_user,
                expires_at=serializer.validated_data.get('expires_at')
            )
            
            audit_log(
                user=request.user,
                action='role_assigned',
                resource_type='user_role',
                resource_id=user_role.id,
                changes={
                    'user': user.username,
                    'role': role.name,
                    'service': role.service.name,
                    'expires_at': str(user_role.expires_at) if user_role.expires_at else None,
                    'reason': serializer.validated_data.get('reason', '')
                },
                request=request
            )
            
            # Clear cache
            RedisService.invalidate_user_cache(user.id)
        
        return Response(
            UserRoleSerializer(user_role).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['delete'], url_path='roles/(?P<role_id>[^/.]+)')
    def revoke_role(self, request, pk=None, role_id=None):
        """Revoke role from user"""
        user = self.get_object()
        user_role = get_object_or_404(UserRole, id=role_id, user=user)
        
        with transaction.atomic():
            audit_log(
                user=request.user,
                action='role_revoked',
                resource_type='user_role',
                resource_id=user_role.id,
                changes={
                    'user': user.username,
                    'role': user_role.role.name,
                    'service': user_role.role.service.name
                },
                request=request
            )
            
            user_role.delete()
            
            # Clear cache
            RedisService.invalidate_user_cache(user.id)
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class ServiceViewSet(ReadOnlyModelViewSet):
    """
    Read-only API for services
    """
    authentication_classes = [JWTCookieAuthentication]
    queryset = Service.objects.filter(is_active=True)
    serializer_class = ServiceSerializer
    permission_classes = [IsIdentityAdmin]
    pagination_class = None  # No pagination for services


class RoleViewSet(ReadOnlyModelViewSet):
    """
    Read-only API for roles
    """
    authentication_classes = [JWTCookieAuthentication]
    serializer_class = RoleSerializer
    permission_classes = [IsIdentityAdmin]
    pagination_class = None  # No pagination for roles
    
    def get_queryset(self):
        queryset = Role.objects.select_related('service').order_by('service__name', 'name')
        
        # Filter by service
        service = self.request.query_params.get('service')
        if service:
            queryset = queryset.filter(service__name=service)
        
        # Filter by is_global
        is_global = self.request.query_params.get('is_global')
        if is_global is not None:
            queryset = queryset.filter(is_global=is_global.lower() == 'true')
        
        return queryset


class BulkOperationsView(APIView):
    """
    API for bulk operations
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsIdentityAdmin]
    
    def post(self, request):
        """Bulk assign roles"""
        serializer = BulkAssignRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        assignments = serializer.validated_data['assignments']
        expires_at = serializer.validated_data.get('expires_at')
        
        created = []
        errors = []
        
        with transaction.atomic():
            django_user = get_django_user(request)
            if not django_user:
                return Response(
                    {"error": "Unable to identify current user"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            for assignment in assignments:
                try:
                    # Check if already assigned
                    existing = UserRole.objects.filter(
                        user=assignment['user'],
                        role=assignment['role']
                    ).exclude(
                        expires_at__lt=timezone.now()
                    ).first()
                    
                    if existing:
                        errors.append({
                            'user': assignment['user'].username,
                            'role': assignment['role'].name,
                            'error': 'Role already assigned'
                        })
                        continue
                    
                    user_role = UserRole.objects.create(
                        user=assignment['user'],
                        role=assignment['role'],
                        granted_by=django_user,
                        expires_at=expires_at
                    )
                    
                    created.append({
                        'user': assignment['user'].username,
                        'role': assignment['role'].name,
                        'id': user_role.id
                    })
                    
                    # Clear cache
                    RedisService.invalidate_user_cache(assignment['user'].id)
                    
                except Exception as e:
                    errors.append({
                        'user': assignment['user'].username,
                        'role': assignment['role'].name,
                        'error': str(e)
                    })
            
            # Audit log
            audit_log(
                user=request.user,
                action='bulk_roles_assigned',
                resource_type='user_role',
                resource_id=None,
                changes={
                    'created': created,
                    'errors': errors,
                    'total': len(assignments)
                },
                request=request
            )
        
        return Response({
            'created': created,
            'errors': errors,
            'total': len(assignments),
            'success': len(created)
        }, status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST)


class AuditLogView(APIView):
    """
    API for viewing audit logs
    """
    authentication_classes = [JWTCookieAuthentication]
    permission_classes = [IsIdentityAdmin]
    
    def get(self, request):
        """List audit logs"""
        # This is a placeholder - implement based on your audit log storage
        # For now, return empty list
        return Response({
            'results': [],
            'count': 0
        })