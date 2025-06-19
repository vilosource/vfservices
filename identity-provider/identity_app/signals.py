"""
Django signals for RBAC-ABAC cache management
"""

import logging
from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserRole, UserAttribute, Service, Role
from .services import RedisService

logger = logging.getLogger(__name__)


@receiver(post_save, sender=UserRole)
def handle_user_role_save(sender, instance, created, **kwargs):
    """
    Update Redis cache when a user role is created or updated.
    """
    if instance.role and instance.role.service:
        user_id = instance.user_id
        service_name = instance.role.service.name
        
        logger.debug(f"UserRole saved: invalidating cache for user {user_id}, service {service_name}")
        RedisService.invalidate_user_cache(user_id, service_name)
        
        # Repopulate if role is active
        if instance.is_active:
            RedisService.populate_user_attributes(user_id, service_name)


@receiver(post_delete, sender=UserRole)
def handle_user_role_delete(sender, instance, **kwargs):
    """
    Update Redis cache when a user role is deleted.
    """
    if instance.role and instance.role.service:
        user_id = instance.user_id
        service_name = instance.role.service.name
        
        logger.debug(f"UserRole deleted: invalidating cache for user {user_id}, service {service_name}")
        RedisService.invalidate_user_cache(user_id, service_name)
        
        # Repopulate to reflect the removal
        RedisService.populate_user_attributes(user_id, service_name)


@receiver(post_save, sender=UserAttribute)
def handle_user_attribute_save(sender, instance, created, **kwargs):
    """
    Update Redis cache when a user attribute is created or updated.
    """
    user_id = instance.user_id
    
    if instance.service:
        # Service-specific attribute
        service_name = instance.service.name
        logger.debug(f"UserAttribute saved: invalidating cache for user {user_id}, service {service_name}")
        RedisService.invalidate_user_cache(user_id, service_name)
        RedisService.populate_user_attributes(user_id, service_name)
    else:
        # Global attribute - invalidate all services
        logger.debug(f"Global UserAttribute saved: invalidating all caches for user {user_id}")
        RedisService.invalidate_user_cache(user_id)
        
        # Repopulate for all services the user has roles in
        user_services = Service.objects.filter(
            roles__user_assignments__user_id=user_id,
            is_active=True
        ).distinct()
        
        for service in user_services:
            RedisService.populate_user_attributes(user_id, service.name)


@receiver(post_delete, sender=UserAttribute)
def handle_user_attribute_delete(sender, instance, **kwargs):
    """
    Update Redis cache when a user attribute is deleted.
    """
    user_id = instance.user_id
    
    if instance.service:
        # Service-specific attribute
        service_name = instance.service.name
        logger.debug(f"UserAttribute deleted: invalidating cache for user {user_id}, service {service_name}")
        RedisService.invalidate_user_cache(user_id, service_name)
        RedisService.populate_user_attributes(user_id, service_name)
    else:
        # Global attribute - handle like save
        handle_user_attribute_save(sender, instance, created=False, **kwargs)


@receiver(post_save, sender=Service)
def handle_service_save(sender, instance, created, **kwargs):
    """
    Handle service activation/deactivation.
    """
    if not created and 'is_active' in (kwargs.get('update_fields') or []):
        if instance.is_active:
            # Service reactivated - populate all users
            logger.info(f"Service {instance.name} activated: populating all users")
            RedisService.populate_all_users_for_service(instance.name)
        else:
            # Service deactivated - invalidate all users
            logger.info(f"Service {instance.name} deactivated: invalidating all users")
            user_ids = UserRole.objects.filter(
                role__service=instance
            ).values_list('user_id', flat=True).distinct()
            
            for user_id in user_ids:
                RedisService.invalidate_user_cache(user_id, instance.name)


@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """
    Update Redis cache when user details change.
    """
    if not created:
        # User updated - check if username or email changed
        if kwargs.get('update_fields'):
            if 'username' in kwargs['update_fields'] or 'email' in kwargs['update_fields']:
                logger.debug(f"User {instance.id} details changed: invalidating all caches")
                RedisService.invalidate_user_cache(instance.id)
                
                # Repopulate for all services
                user_services = Service.objects.filter(
                    roles__user_assignments__user_id=instance.id,
                    is_active=True
                ).distinct()
                
                for service in user_services:
                    RedisService.populate_user_attributes(instance.id, service.name)


# Connect signals
def connect_signals():
    """
    Ensure all signals are connected.
    
    Call this from AppConfig.ready() to ensure signals are registered.
    """
    logger.info("RBAC-ABAC signals connected")