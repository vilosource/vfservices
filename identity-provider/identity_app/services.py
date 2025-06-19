"""
Services for managing RBAC-ABAC data and Redis synchronization
"""

import json
import logging
from typing import Dict, List, Optional, Any
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils import timezone
from common.rbac_abac import RedisAttributeClient, UserAttributes as ABACUserAttributes
from .models import (
    Service, Role, UserRole, ServiceAttribute, 
    UserAttribute, ServiceManifest
)

logger = logging.getLogger(__name__)


class RBACService:
    """Service for managing roles and permissions."""
    
    @staticmethod
    def get_user_roles(user: User, service: Service = None) -> List[UserRole]:
        """
        Get active roles for a user, optionally filtered by service.
        
        Args:
            user: The user to get roles for
            service: Optional service to filter by
            
        Returns:
            List of active UserRole objects
        """
        queryset = UserRole.objects.filter(
            user=user,
            role__service__is_active=True
        ).select_related('role', 'role__service')
        
        # Filter out expired roles
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        if service:
            queryset = queryset.filter(role__service=service)
        
        return list(queryset)
    
    @staticmethod
    def assign_role(user: User, role: Role, granted_by: User,
                   resource_id: str = None, expires_at: timezone.datetime = None) -> UserRole:
        """
        Assign a role to a user.
        
        Args:
            user: User to assign role to
            role: Role to assign
            granted_by: User granting the role
            resource_id: Optional resource ID for scoped roles
            expires_at: Optional expiration time
            
        Returns:
            Created UserRole object
        """
        user_role, created = UserRole.objects.update_or_create(
            user=user,
            role=role,
            resource_id=resource_id,
            defaults={
                'granted_by': granted_by,
                'expires_at': expires_at
            }
        )
        
        if created:
            logger.info(f"Assigned role {role} to user {user.username}")
        else:
            logger.info(f"Updated role {role} for user {user.username}")
        
        # Invalidate Redis cache
        RedisService.invalidate_user_cache(user.id, role.service.name)
        
        return user_role
    
    @staticmethod
    def revoke_role(user: User, role: Role, resource_id: str = None):
        """
        Revoke a role from a user.
        
        Args:
            user: User to revoke role from
            role: Role to revoke
            resource_id: Optional resource ID for scoped roles
        """
        deleted_count, _ = UserRole.objects.filter(
            user=user,
            role=role,
            resource_id=resource_id
        ).delete()
        
        if deleted_count > 0:
            logger.info(f"Revoked role {role} from user {user.username}")
            # Invalidate Redis cache
            RedisService.invalidate_user_cache(user.id, role.service.name)


class AttributeService:
    """Service for managing user attributes."""
    
    @staticmethod
    def get_user_attributes(user: User, service: Service = None) -> Dict[str, Any]:
        """
        Get all attributes for a user.
        
        Args:
            user: User to get attributes for
            service: Optional service to get attributes for
            
        Returns:
            Dictionary of attribute name to value
        """
        # Start with global attributes
        attributes = {}
        
        # Get global attributes
        global_attrs = UserAttribute.objects.filter(
            user=user,
            service__isnull=True
        )
        
        for attr in global_attrs:
            attributes[attr.name] = attr.get_value()
        
        # Get service-specific attributes if requested
        if service:
            service_attrs = UserAttribute.objects.filter(
                user=user,
                service=service
            )
            
            for attr in service_attrs:
                attributes[attr.name] = attr.get_value()
            
            # Add default values for missing required attributes
            required_attrs = ServiceAttribute.objects.filter(
                service=service,
                is_required=True
            )
            
            for req_attr in required_attrs:
                if req_attr.name not in attributes:
                    default_value = req_attr.get_default_value()
                    if default_value is not None:
                        attributes[req_attr.name] = default_value
        
        return attributes
    
    @staticmethod
    def set_user_attribute(user: User, name: str, value: Any, 
                         service: Service = None, updated_by: User = None) -> UserAttribute:
        """
        Set a user attribute.
        
        Args:
            user: User to set attribute for
            name: Attribute name
            value: Attribute value
            service: Optional service (None for global)
            updated_by: User making the update
            
        Returns:
            Created/updated UserAttribute object
        """
        attr, created = UserAttribute.objects.update_or_create(
            user=user,
            service=service,
            name=name,
            defaults={
                'updated_by': updated_by
            }
        )
        
        attr.set_value(value)
        attr.save()
        
        action = "Created" if created else "Updated"
        logger.info(f"{action} attribute {name} for user {user.username}")
        
        # Invalidate Redis cache
        service_name = service.name if service else None
        RedisService.invalidate_user_cache(user.id, service_name)
        
        return attr


class RedisService:
    """Service for managing Redis cache of user attributes and roles."""
    
    @classmethod
    def get_client(cls) -> RedisAttributeClient:
        """Get or create Redis client instance."""
        if not hasattr(cls, '_client'):
            cls._client = RedisAttributeClient()
        return cls._client
    
    @classmethod
    def populate_user_attributes(cls, user_id: int, service_name: str) -> bool:
        """
        Populate Redis with user attributes for a specific service.
        
        Args:
            user_id: User ID
            service_name: Service name
            
        Returns:
            True if successful
        """
        try:
            user = User.objects.get(id=user_id)
            service = Service.objects.get(name=service_name, is_active=True)
        except (User.DoesNotExist, Service.DoesNotExist) as e:
            logger.error(f"Failed to populate attributes: {e}")
            return False
        
        # Get user roles for this service
        user_roles = RBACService.get_user_roles(user, service)
        role_names = [ur.role.name for ur in user_roles]
        
        # Get user attributes
        attributes = AttributeService.get_user_attributes(user, service)
        
        # Build UserAttributes object
        user_attrs = ABACUserAttributes(
            user_id=user.id,
            username=user.username,
            email=user.email,
            roles=role_names,
            department=attributes.get('department'),
            admin_group_ids=attributes.get('admin_group_ids', []),
            customer_ids=attributes.get('customer_ids', []),
            assigned_doc_ids=attributes.get('assigned_doc_ids', []),
            service_specific_attrs=attributes
        )
        
        # Store in Redis
        client = cls.get_client()
        success = client.set_user_attributes(user_id, service_name, user_attrs)
        
        if success:
            logger.info(f"Populated Redis attributes for user {user_id} in service {service_name}")
        else:
            logger.error(f"Failed to populate Redis attributes for user {user_id}")
        
        return success
    
    @classmethod
    def invalidate_user_cache(cls, user_id: int, service_name: str = None):
        """
        Invalidate user cache and publish invalidation message.
        
        Args:
            user_id: User ID
            service_name: Optional service name (None for all services)
        """
        client = cls.get_client()
        
        # Delete from cache
        deleted = client.invalidate_user_attributes(user_id, service_name)
        logger.info(f"Invalidated {deleted} cache entries for user {user_id}")
        
        # Publish invalidation message
        client.publish_invalidation(user_id, service_name)
    
    @classmethod
    def populate_all_users_for_service(cls, service_name: str) -> int:
        """
        Populate Redis with all user attributes for a service.
        
        Useful after service registration or bulk updates.
        
        Args:
            service_name: Service to populate for
            
        Returns:
            Number of users populated
        """
        try:
            service = Service.objects.get(name=service_name, is_active=True)
        except Service.DoesNotExist:
            logger.error(f"Service {service_name} not found")
            return 0
        
        # Get all users with roles in this service
        user_ids = UserRole.objects.filter(
            role__service=service,
            role__service__is_active=True
        ).values_list('user_id', flat=True).distinct()
        
        count = 0
        for user_id in user_ids:
            if cls.populate_user_attributes(user_id, service_name):
                count += 1
        
        logger.info(f"Populated {count} users for service {service_name}")
        return count


class ManifestService:
    """Service for handling service manifest registration."""
    
    @staticmethod
    @transaction.atomic
    def register_manifest(manifest_data: Dict[str, Any], ip_address: str = None) -> ServiceManifest:
        """
        Register or update a service manifest.
        
        Args:
            manifest_data: Manifest JSON data
            ip_address: IP address of the submitter
            
        Returns:
            Created ServiceManifest object
        """
        service_info = manifest_data.get('service')
        if not service_info:
            raise ValueError("Manifest must include 'service' field")
        
        # Extract service details
        if isinstance(service_info, dict):
            service_name = service_info.get('name')
            display_name = service_info.get('display_name', service_name)
            description = service_info.get('description', '')
        else:
            # Backward compatibility - if service is just a string
            service_name = service_info
            display_name = service_name
            description = ''
        
        if not service_name:
            raise ValueError("Service name is required")
        
        # Create or update service
        service, created = Service.objects.update_or_create(
            name=service_name,
            defaults={
                'display_name': display_name,
                'description': description,
                'manifest_version': manifest_data.get('version', '1.0')
            }
        )
        
        # Deactivate previous manifests
        ServiceManifest.objects.filter(
            service=service,
            is_active=True
        ).update(is_active=False)
        
        # Get next version number
        last_version = ServiceManifest.objects.filter(
            service=service
        ).order_by('-version').first()
        
        next_version = 1 if not last_version else last_version.version + 1
        
        # Create new manifest
        manifest = ServiceManifest.objects.create(
            service=service,
            version=next_version,
            manifest_data=manifest_data,
            submitted_by_ip=ip_address,
            is_active=True
        )
        
        # Process roles
        roles_data = manifest_data.get('roles', [])
        for role_data in roles_data:
            Role.objects.update_or_create(
                service=service,
                name=role_data['name'],
                defaults={
                    'display_name': role_data.get('display_name', role_data['name']),
                    'description': role_data.get('description', ''),
                    'is_global': role_data.get('is_global', True)
                }
            )
        
        # Process attributes
        attrs_data = manifest_data.get('attributes', [])
        for attr_data in attrs_data:
            ServiceAttribute.objects.update_or_create(
                service=service,
                name=attr_data['name'],
                defaults={
                    'display_name': attr_data.get('display_name', attr_data['name']),
                    'description': attr_data.get('description', ''),
                    'attribute_type': attr_data.get('type', 'string'),
                    'is_required': attr_data.get('required', False),
                    'default_value': json.dumps(attr_data.get('default'))
                        if 'default' in attr_data else None
                }
            )
        
        logger.info(f"Registered manifest v{next_version} for service {service_name}")
        
        # Populate Redis for all users of this service
        RedisService.populate_all_users_for_service(service_name)
        
        # Return a dict representation for the API response
        return {
            'service': service.name,
            'version': manifest.version,
            'registered_at': manifest.submitted_at.isoformat(),
            'is_active': manifest.is_active
        }