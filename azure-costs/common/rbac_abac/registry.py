"""
Policy Registry for ABAC

This module implements the Strategy pattern for authorization policies.
Policies are registered using a decorator and stored in a global registry.
"""

from typing import Dict, Callable, Optional, Any
import functools
import logging

logger = logging.getLogger(__name__)

# Global registry for ABAC policy functions
POLICY_REGISTRY: Dict[str, Callable] = {}


def register_policy(name: str) -> Callable:
    """
    Decorator to register an ABAC policy function by name.
    
    Usage:
        @register_policy('ownership_check')
        def ownership_check(user_attrs, obj=None, action=None):
            return obj.owner_id == user_attrs.user_id
    
    Args:
        name: Unique name for the policy
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        if name in POLICY_REGISTRY:
            logger.warning(f"Policy '{name}' is being overwritten in registry")
        
        # Add metadata to the function
        func._policy_name = name
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Policy '{name}' executed successfully")
                return result
            except Exception as e:
                logger.error(f"Error executing policy '{name}': {str(e)}")
                # Secure default: deny on error
                return False
        
        # Store the wrapper in the registry, not the original function
        POLICY_REGISTRY[name] = wrapper
        
        return wrapper
    
    return decorator


def get_policy(name: str) -> Optional[Callable]:
    """
    Retrieve a policy function from the registry.
    
    Args:
        name: Name of the policy
        
    Returns:
        Policy function or None if not found
    """
    policy = POLICY_REGISTRY.get(name)
    if not policy:
        logger.warning(f"Policy '{name}' not found in registry")
    return policy


def list_policies() -> Dict[str, str]:
    """
    List all registered policies with their docstrings.
    
    Returns:
        Dict mapping policy names to their descriptions
    """
    policies = {}
    for name, func in POLICY_REGISTRY.items():
        doc = func.__doc__ or "No description available"
        policies[name] = doc.strip()
    return policies


def clear_registry():
    """Clear all registered policies. Useful for testing."""
    POLICY_REGISTRY.clear()
    logger.info("Policy registry cleared")