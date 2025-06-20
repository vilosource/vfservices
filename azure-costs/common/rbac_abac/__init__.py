"""
RBAC-ABAC Authorization Library for VF Services

This library provides a hybrid Role-Based Access Control (RBAC) and 
Attribute-Based Access Control (ABAC) system for the VF Services microservices architecture.

Core Components:
- Policy Registry: Decorator-based registration of authorization rules
- ABACModelMixin: Django model mixin for permission checks
- Custom QuerySet: Database-level filtering for performance
- DRF Permissions: Integration with Django REST Framework
- Redis Integration: Fast attribute caching and pub/sub
"""

from .registry import register_policy, POLICY_REGISTRY, get_policy
from .mixins import ABACModelMixin
from .querysets import ABACQuerySet, ABACManager
from .permissions import ABACPermission, RoleRequired, ServicePermission
from .redis_client import RedisAttributeClient, get_user_attributes
from .models import UserAttributes

# Import policies to register them
from . import policies

__all__ = [
    'register_policy',
    'POLICY_REGISTRY',
    'get_policy',
    'ABACModelMixin',
    'ABACQuerySet',
    'ABACManager',
    'ABACPermission',
    'RoleRequired',
    'ServicePermission',
    'RedisAttributeClient',
    'get_user_attributes',
    'UserAttributes',
]

__version__ = '1.0.0'