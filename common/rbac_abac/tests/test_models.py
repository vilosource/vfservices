"""
Tests for RBAC-ABAC data models
"""

import pytest
import json
from common.rbac_abac.models import UserAttributes


class TestUserAttributes:
    
    def test_basic_initialization(self):
        """Test creating UserAttributes with basic fields."""
        attrs = UserAttributes(
            user_id=1,
            username='testuser',
            email='test@example.com',
            roles=['user', 'editor']
        )
        
        assert attrs.user_id == 1
        assert attrs.username == 'testuser'
        assert attrs.email == 'test@example.com'
        assert attrs.roles == ['user', 'editor']
        assert attrs.department is None
        assert attrs.admin_group_ids == []
    
    def test_full_initialization(self):
        """Test creating UserAttributes with all fields."""
        attrs = UserAttributes(
            user_id=1,
            username='testuser',
            email='test@example.com',
            roles=['admin'],
            department='Engineering',
            admin_group_ids=[1, 2, 3],
            customer_ids=[10, 20],
            assigned_doc_ids=[100, 200],
            service_specific_attrs={'billing': {'limit': 1000}}
        )
        
        assert attrs.department == 'Engineering'
        assert attrs.admin_group_ids == [1, 2, 3]
        assert attrs.customer_ids == [10, 20]
        assert attrs.assigned_doc_ids == [100, 200]
        assert attrs.service_specific_attrs == {'billing': {'limit': 1000}}
    
    def test_to_redis_data(self):
        """Test converting to Redis storage format."""
        attrs = UserAttributes(
            user_id=1,
            username='testuser',
            email='test@example.com',
            roles=['user', 'admin'],
            department='Sales',
            admin_group_ids=[5, 7]
        )
        
        redis_data = attrs.to_redis_data()
        
        assert redis_data['user_id'] == '1'
        assert redis_data['username'] == 'testuser'
        assert redis_data['email'] == 'test@example.com'
        assert redis_data['department'] == 'Sales'
        assert json.loads(redis_data['roles']) == ['user', 'admin']
        assert json.loads(redis_data['admin_group_ids']) == [5, 7]
    
    def test_from_redis_data(self):
        """Test creating from Redis data."""
        redis_data = {
            b'user_id': b'42',
            b'username': b'testuser',
            b'email': b'test@example.com',
            b'roles': b'["admin", "editor"]',
            b'department': b'IT',
            b'admin_group_ids': b'[1, 2, 3]',
            b'customer_ids': b'[]',
            b'assigned_doc_ids': b'[10, 20]',
            b'service_specific_attrs': b'{"inventory": {"warehouse": "A"}}'
        }
        
        attrs = UserAttributes.from_redis_data(redis_data)
        
        assert attrs.user_id == 42
        assert attrs.username == 'testuser'
        assert attrs.email == 'test@example.com'
        assert attrs.roles == ['admin', 'editor']
        assert attrs.department == 'IT'
        assert attrs.admin_group_ids == [1, 2, 3]
        assert attrs.customer_ids == []
        assert attrs.assigned_doc_ids == [10, 20]
        assert attrs.service_specific_attrs == {'inventory': {'warehouse': 'A'}}
    
    def test_from_redis_data_with_missing_fields(self):
        """Test creating from partial Redis data."""
        redis_data = {
            b'user_id': b'1',
            b'username': b'testuser',
            b'email': b'test@example.com'
        }
        
        attrs = UserAttributes.from_redis_data(redis_data)
        
        assert attrs.user_id == 1
        assert attrs.username == 'testuser'
        assert attrs.email == 'test@example.com'
        assert attrs.roles == []
        assert attrs.department is None
    
    def test_from_redis_data_with_invalid_json(self):
        """Test handling invalid JSON in Redis data."""
        redis_data = {
            b'user_id': b'1',
            b'username': b'testuser',
            b'email': b'test@example.com',
            b'roles': b'invalid json',
            b'service_specific_attrs': b'not json either'
        }
        
        attrs = UserAttributes.from_redis_data(redis_data)
        
        assert attrs.roles == []  # Falls back to empty list
        assert attrs.service_specific_attrs == {}  # Falls back to empty dict
    
    def test_has_role(self):
        """Test role checking methods."""
        attrs = UserAttributes(
            user_id=1,
            username='testuser',
            email='test@example.com',
            roles=['user', 'editor', 'reviewer']
        )
        
        assert attrs.has_role('editor') == True
        assert attrs.has_role('admin') == False
        
        assert attrs.has_any_role(['admin', 'editor']) == True
        assert attrs.has_any_role(['admin', 'manager']) == False
        
        assert attrs.has_all_roles(['user', 'editor']) == True
        assert attrs.has_all_roles(['user', 'admin']) == False
    
    def test_get_service_attr(self):
        """Test getting service-specific attributes."""
        attrs = UserAttributes(
            user_id=1,
            username='testuser',
            email='test@example.com',
            service_specific_attrs={
                'billing': {'credit_limit': 5000, 'currency': 'USD'},
                'inventory': {'warehouse': 'A'}
            }
        )
        
        assert attrs.get_service_attr('billing', 'credit_limit') == 5000
        assert attrs.get_service_attr('billing', 'currency') == 'USD'
        assert attrs.get_service_attr('inventory', 'warehouse') == 'A'
        
        # Test missing service
        assert attrs.get_service_attr('unknown', 'attr') is None
        assert attrs.get_service_attr('unknown', 'attr', 'default') == 'default'
        
        # Test missing attribute
        assert attrs.get_service_attr('billing', 'unknown') is None
        assert attrs.get_service_attr('billing', 'unknown', 100) == 100
    
    def test_round_trip_conversion(self):
        """Test converting to Redis and back maintains data integrity."""
        original = UserAttributes(
            user_id=123,
            username='testuser',
            email='test@example.com',
            roles=['admin', 'user'],
            department='Engineering',
            admin_group_ids=[1, 2, 3],
            customer_ids=[10, 20, 30],
            assigned_doc_ids=[100],
            service_specific_attrs={'test': {'nested': 'value'}}
        )
        
        # Convert to Redis format
        redis_data = original.to_redis_data()
        
        # Convert back (simulating bytes from Redis)
        redis_bytes = {k.encode(): v.encode() for k, v in redis_data.items()}
        restored = UserAttributes.from_redis_data(redis_bytes)
        
        # Verify all fields match
        assert restored.user_id == original.user_id
        assert restored.username == original.username
        assert restored.email == original.email
        assert restored.roles == original.roles
        assert restored.department == original.department
        assert restored.admin_group_ids == original.admin_group_ids
        assert restored.customer_ids == original.customer_ids
        assert restored.assigned_doc_ids == original.assigned_doc_ids
        assert restored.service_specific_attrs == original.service_specific_attrs