"""
Django model mixins for ABAC integration
"""

from typing import Dict, Optional, Any
import logging
from django.db import models
from .registry import get_policy
from .models import UserAttributes

logger = logging.getLogger(__name__)


class ABACModelMixin:
    """
    Mixin for Django models to add ABAC capabilities.
    
    This mixin provides:
    - check_abac() method for permission checks
    - Policy mapping via ABAC_POLICIES class attribute
    - Template Method pattern for extensibility
    
    Usage:
        class Document(ABACModelMixin, models.Model):
            owner = models.ForeignKey(User, on_delete=models.CASCADE)
            
            ABAC_POLICIES = {
                'view': 'ownership_check',
                'edit': 'ownership_or_admin',
                'delete': 'admin_only'
            }
    """
    
    # Each model can define a mapping of action -> policy name
    # For example: {'view': 'ownership_check', 'edit': 'department_match'}
    ABAC_POLICIES: Dict[str, str] = {}
    
    def check_abac(self, user_attrs: UserAttributes, action: str) -> bool:
        """
        Check if the given user is allowed to perform action on this object.
        
        This method implements the Template Method pattern:
        1. Find the policy name for the action
        2. Look up the policy function
        3. Execute the policy with user attributes and object
        
        Args:
            user_attrs: UserAttributes object containing user info
            action: Action to check (e.g., 'view', 'edit', 'delete')
            
        Returns:
            True if action is allowed, False otherwise
        """
        if not isinstance(user_attrs, UserAttributes):
            logger.warning(f"Invalid user_attrs type: {type(user_attrs)}")
            return False
        
        # Get policy name for this action
        policy_name = self._get_policy_name(action)
        if not policy_name:
            logger.debug(f"No policy defined for action '{action}' on {self.__class__.__name__}")
            return self._default_permission(user_attrs, action)
        
        # Look up the policy function
        policy_func = get_policy(policy_name)
        if policy_func is None:
            logger.error(f"Policy '{policy_name}' not found in registry")
            return False  # Secure default: deny if policy not found
        
        # Execute the policy
        try:
            result = bool(policy_func(user_attrs, obj=self, action=action))
            logger.debug(
                f"ABAC check: user={user_attrs.user_id}, "
                f"action={action}, object={self.__class__.__name__}({self.pk}), "
                f"policy={policy_name}, result={result}"
            )
            return result
        except Exception as e:
            logger.error(
                f"Error executing policy '{policy_name}' for {self.__class__.__name__}: {str(e)}"
            )
            return False  # Secure default: deny on error
    
    def _get_policy_name(self, action: str) -> Optional[str]:
        """
        Get the policy name for a given action.
        
        This method can be overridden by subclasses for dynamic policy selection.
        
        Args:
            action: The action to get policy for
            
        Returns:
            Policy name or None
        """
        if hasattr(self.__class__, 'ABAC_POLICIES'):
            return self.ABAC_POLICIES.get(action)
        return None
    
    def _default_permission(self, user_attrs: UserAttributes, action: str) -> bool:
        """
        Default permission when no policy is defined.
        
        Override this method to change default behavior.
        Default implementation denies all actions.
        
        Args:
            user_attrs: User attributes
            action: Action being checked
            
        Returns:
            True to allow, False to deny
        """
        return False  # Secure default: deny
    
    def get_allowed_actions(self, user_attrs: UserAttributes) -> list:
        """
        Get list of actions the user is allowed to perform on this object.
        
        Useful for UI to show/hide action buttons.
        
        Args:
            user_attrs: User attributes
            
        Returns:
            List of allowed action names
        """
        allowed = []
        for action in self.ABAC_POLICIES.keys():
            if self.check_abac(user_attrs, action):
                allowed.append(action)
        return allowed
    
    @classmethod
    def get_required_policies(cls) -> Dict[str, str]:
        """
        Get all policies required by this model.
        
        Useful for validation and documentation.
        
        Returns:
            Dict mapping actions to policy names
        """
        return cls.ABAC_POLICIES.copy()


class ABACModelMetaclass(models.base.ModelBase):
    """
    Metaclass to validate ABAC configuration at model definition time.
    
    This ensures models using ABACModelMixin are properly configured.
    """
    
    def __new__(cls, name, bases, attrs):
        new_class = super().__new__(cls, name, bases, attrs)
        
        # Skip validation for the mixin itself
        if name == 'ABACModelMixin':
            return new_class
        
        # Check if this model uses ABACModelMixin
        if any(isinstance(base, type) and issubclass(base, ABACModelMixin) for base in bases):
            # Validate ABAC_POLICIES if defined
            if 'ABAC_POLICIES' in attrs:
                policies = attrs['ABAC_POLICIES']
                if not isinstance(policies, dict):
                    raise TypeError(
                        f"{name}.ABAC_POLICIES must be a dict, got {type(policies).__name__}"
                    )
                
                for action, policy_name in policies.items():
                    if not isinstance(action, str) or not isinstance(policy_name, str):
                        raise TypeError(
                            f"{name}.ABAC_POLICIES must map strings to strings"
                        )
        
        return new_class