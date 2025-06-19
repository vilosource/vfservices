"""
Data models for RBAC-ABAC system
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class UserAttributes:
    """
    Container for user attributes loaded from Redis.
    
    This class holds all user information needed for authorization decisions,
    including roles and custom attributes.
    """
    user_id: int
    username: str
    email: str
    roles: List[str] = field(default_factory=list)
    department: Optional[str] = None
    admin_group_ids: List[int] = field(default_factory=list)
    customer_ids: List[int] = field(default_factory=list)
    assigned_doc_ids: List[int] = field(default_factory=list)
    service_specific_attrs: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_redis_data(cls, data: Dict[bytes, bytes]) -> 'UserAttributes':
        """
        Create UserAttributes from Redis hash data.
        
        Args:
            data: Raw data from Redis HGETALL
            
        Returns:
            UserAttributes instance
        """
        # Decode bytes keys/values
        decoded = {}
        for key, value in data.items():
            if isinstance(key, bytes):
                key = key.decode('utf-8')
            if isinstance(value, bytes):
                value = value.decode('utf-8')
            
            # Parse JSON fields
            if key in ['roles', 'admin_group_ids', 'customer_ids', 'assigned_doc_ids', 'service_specific_attrs']:
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    if key == 'service_specific_attrs':
                        value = {}
                    else:
                        value = []
            
            decoded[key] = value
        
        # Convert string IDs to integers where needed
        if 'user_id' in decoded and isinstance(decoded['user_id'], str):
            decoded['user_id'] = int(decoded['user_id'])
        
        return cls(**decoded)
    
    def to_redis_data(self) -> Dict[str, str]:
        """
        Convert to format suitable for Redis storage.
        
        Returns:
            Dict with string keys/values for Redis HMSET
        """
        data = {
            'user_id': str(self.user_id),
            'username': self.username,
            'email': self.email,
            'roles': json.dumps(self.roles),
            'admin_group_ids': json.dumps(self.admin_group_ids),
            'customer_ids': json.dumps(self.customer_ids),
            'assigned_doc_ids': json.dumps(self.assigned_doc_ids),
            'service_specific_attrs': json.dumps(self.service_specific_attrs),
        }
        
        # Add optional fields
        if self.department:
            data['department'] = self.department
            
        return data
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def has_all_roles(self, roles: List[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(role in self.roles for role in roles)
    
    def get_service_attr(self, service: str, attr: str, default=None):
        """Get a service-specific attribute."""
        return self.service_specific_attrs.get(service, {}).get(attr, default)