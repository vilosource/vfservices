"""
Custom QuerySet and Manager for ABAC filtering
"""

from typing import Optional, List, Dict, Any
import logging
from django.db import models
from django.db.models import Q
from .models import UserAttributes
from .registry import get_policy

logger = logging.getLogger(__name__)


class ABACQuerySet(models.QuerySet):
    """
    Custom QuerySet that adds ABAC filtering capabilities.
    
    This QuerySet provides the abac_filter() method to efficiently
    filter objects based on ABAC policies at the database level.
    """
    
    def abac_filter(self, user_attrs: UserAttributes, action: str) -> 'ABACQuerySet':
        """
        Filter the queryset to only include objects where user is allowed to perform action.
        
        This method attempts to translate ABAC policies into database queries
        for efficient filtering. If a policy cannot be translated, it falls
        back to Python-level filtering (less efficient).
        
        Args:
            user_attrs: UserAttributes object with user information
            action: Action to check (e.g., 'view', 'edit')
            
        Returns:
            Filtered QuerySet
        """
        model_cls = self.model
        
        # Check if model has ABAC policies
        if not hasattr(model_cls, 'ABAC_POLICIES'):
            logger.warning(f"Model {model_cls.__name__} does not define ABAC_POLICIES")
            return self.none()
        
        policy_name = model_cls.ABAC_POLICIES.get(action)
        if not policy_name:
            logger.debug(f"No policy defined for action '{action}' on {model_cls.__name__}")
            return self.none()
        
        # Try to apply known policy patterns as database filters
        filter_q = self._get_policy_filter(policy_name, user_attrs)
        
        if filter_q is not None:
            # We have a database filter for this policy
            return self.filter(filter_q)
        else:
            # Fall back to Python-level filtering
            logger.warning(
                f"No database filter for policy '{policy_name}', "
                f"falling back to Python filtering (slow)"
            )
            return self._python_filter(user_attrs, action)
    
    def _get_policy_filter(self, policy_name: str, user_attrs: UserAttributes) -> Optional[Q]:
        """
        Translate a policy name into a Q object for database filtering.
        
        This method contains the mapping of known policies to their
        database query equivalents. Add new mappings here as policies
        are created.
        
        Args:
            policy_name: Name of the policy
            user_attrs: User attributes
            
        Returns:
            Q object for filtering, or None if policy cannot be translated
        """
        # Map of policy names to filter builders
        policy_filters = {
            'ownership_check': self._ownership_filter,
            'ownership_or_admin': self._ownership_or_admin_filter,
            'department_match': self._department_filter,
            'group_membership': self._group_membership_filter,
            'public_access': self._public_access_filter,
        }
        
        filter_builder = policy_filters.get(policy_name)
        if filter_builder:
            return filter_builder(user_attrs)
        
        # Check for custom filters defined on the model
        if hasattr(self.model, f'_abac_filter_{policy_name}'):
            custom_filter = getattr(self.model, f'_abac_filter_{policy_name}')
            return custom_filter(user_attrs)
        
        return None
    
    def _ownership_filter(self, user_attrs: UserAttributes) -> Q:
        """Filter for objects owned by the user."""
        return Q(owner_id=user_attrs.user_id) | Q(owner__id=user_attrs.user_id)
    
    def _ownership_or_admin_filter(self, user_attrs: UserAttributes) -> Q:
        """Filter for objects owned by user or where user is admin."""
        q = self._ownership_filter(user_attrs)
        
        # Add admin group check if model has group_id field
        if hasattr(self.model, 'group_id') and user_attrs.admin_group_ids:
            q |= Q(group_id__in=user_attrs.admin_group_ids)
        
        # Add global admin role check
        if 'admin' in user_attrs.roles or f'{self.model._meta.app_label}_admin' in user_attrs.roles:
            return Q()  # Admin sees all
        
        return q
    
    def _department_filter(self, user_attrs: UserAttributes) -> Q:
        """Filter for objects in user's department."""
        # Admin override - check first
        if 'admin' in user_attrs.roles:
            return Q()  # Admin sees all
        
        if not user_attrs.department:
            return Q(pk__in=[])  # No department = no access
        
        # Check for department field variations
        q = Q()
        if hasattr(self.model, 'department'):
            q |= Q(department=user_attrs.department)
        if hasattr(self.model, 'department_id'):
            q |= Q(department_id=user_attrs.department)
        
        return q
    
    def _group_membership_filter(self, user_attrs: UserAttributes) -> Q:
        """Filter for objects where user is a group member."""
        # This assumes a many-to-many relationship with groups
        q = Q()
        
        if hasattr(self.model, 'groups'):
            # User's groups (assuming user has group_ids attribute)
            group_ids = getattr(user_attrs, 'group_ids', [])
            if group_ids:
                q |= Q(groups__id__in=group_ids)
        
        if hasattr(self.model, 'group_id'):
            # Single group field
            if user_attrs.admin_group_ids:
                q |= Q(group_id__in=user_attrs.admin_group_ids)
        
        return q
    
    def _public_access_filter(self, user_attrs: UserAttributes) -> Q:
        """Filter for publicly accessible objects."""
        # Check for various "public" field names
        q = Q()
        if hasattr(self.model, 'is_public'):
            q |= Q(is_public=True)
        if hasattr(self.model, 'public'):
            q |= Q(public=True)
        if hasattr(self.model, 'visibility'):
            q |= Q(visibility='public')
        
        return q
    
    def _python_filter(self, user_attrs: UserAttributes, action: str) -> 'ABACQuerySet':
        """
        Fall back to Python-level filtering when DB filtering isn't possible.
        
        WARNING: This loads all objects into memory and can be very slow
        for large querysets. Use only as a last resort.
        
        Args:
            user_attrs: User attributes
            action: Action to check
            
        Returns:
            Filtered QuerySet
        """
        allowed_ids = []
        
        # Limit to reasonable number to prevent memory issues
        for obj in self[:1000]:  # Arbitrary limit
            if hasattr(obj, 'check_abac') and obj.check_abac(user_attrs, action):
                allowed_ids.append(obj.pk)
        
        if len(self) > 1000:
            logger.warning(
                f"ABAC Python filter limited to 1000 objects out of {len(self)}. "
                f"Consider implementing a database filter for better performance."
            )
        
        return self.filter(pk__in=allowed_ids)
    
    def abac_prefetch(self, user_attrs: UserAttributes, action: str) -> 'ABACQuerySet':
        """
        Optimize queryset for ABAC checks by prefetching related data.
        
        This method can be overridden by specific models to prefetch
        data needed for their policies.
        
        Args:
            user_attrs: User attributes
            action: Action that will be checked
            
        Returns:
            QuerySet with prefetched data
        """
        # Default prefetches based on common patterns
        prefetch_fields = []
        
        if hasattr(self.model, 'owner'):
            prefetch_fields.append('owner')
        if hasattr(self.model, 'group'):
            prefetch_fields.append('group')
        if hasattr(self.model, 'department'):
            prefetch_fields.append('department')
        
        if prefetch_fields:
            return self.select_related(*prefetch_fields)
        
        return self


class ABACManager(models.Manager):
    """
    Custom manager that returns ABACQuerySet.
    
    Usage:
        class Document(ABACModelMixin, models.Model):
            # ... fields ...
            objects = ABACManager()
    """
    
    def get_queryset(self) -> ABACQuerySet:
        """Return ABACQuerySet instead of regular QuerySet."""
        return ABACQuerySet(self.model, using=self._db)
    
    def abac_filter(self, user_attrs: UserAttributes, action: str) -> ABACQuerySet:
        """Convenience method to get filtered queryset."""
        return self.get_queryset().abac_filter(user_attrs, action)
    
    def viewable_by(self, user_attrs: UserAttributes) -> ABACQuerySet:
        """Convenience method for getting viewable objects."""
        return self.abac_filter(user_attrs, 'view')
    
    def editable_by(self, user_attrs: UserAttributes) -> ABACQuerySet:
        """Convenience method for getting editable objects."""
        return self.abac_filter(user_attrs, 'edit')
    
    def deletable_by(self, user_attrs: UserAttributes) -> ABACQuerySet:
        """Convenience method for getting deletable objects."""
        return self.abac_filter(user_attrs, 'delete')