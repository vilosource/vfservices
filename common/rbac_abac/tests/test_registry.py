"""
Tests for the policy registry
"""

import pytest
from common.rbac_abac.registry import (
    register_policy, get_policy, list_policies, 
    clear_registry, POLICY_REGISTRY
)


class TestPolicyRegistry:
    
    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()
    
    def test_register_policy(self):
        """Test basic policy registration."""
        @register_policy('test_policy')
        def test_policy(user_attrs, obj=None, action=None):
            """Test policy function"""
            return True
        
        assert 'test_policy' in POLICY_REGISTRY
        assert POLICY_REGISTRY['test_policy']._policy_name == 'test_policy'
    
    def test_get_policy(self):
        """Test retrieving a registered policy."""
        @register_policy('test_policy')
        def test_policy(user_attrs, obj=None, action=None):
            return True
        
        policy = get_policy('test_policy')
        assert policy is not None
        assert policy(None) == True
    
    def test_get_nonexistent_policy(self):
        """Test retrieving a non-existent policy."""
        policy = get_policy('nonexistent')
        assert policy is None
    
    def test_policy_execution_with_error(self):
        """Test that policies return False on error."""
        @register_policy('error_policy')
        def error_policy(user_attrs, obj=None, action=None):
            raise ValueError("Test error")
        
        policy = get_policy('error_policy')
        result = policy(None)
        assert result == False  # Secure default on error
    
    def test_list_policies(self):
        """Test listing all registered policies."""
        @register_policy('policy1')
        def policy1(user_attrs, obj=None, action=None):
            """Policy 1 description"""
            return True
        
        @register_policy('policy2')
        def policy2(user_attrs, obj=None, action=None):
            """Policy 2 description"""
            return True
        
        policies = list_policies()
        assert len(policies) == 2
        assert policies['policy1'] == 'Policy 1 description'
        assert policies['policy2'] == 'Policy 2 description'
    
    def test_overwrite_policy_warning(self, caplog):
        """Test that overwriting a policy logs a warning."""
        @register_policy('test_policy')
        def policy1(user_attrs, obj=None, action=None):
            return True
        
        @register_policy('test_policy')
        def policy2(user_attrs, obj=None, action=None):
            return False
        
        assert "being overwritten" in caplog.text
        
        # Verify the second policy is active
        policy = get_policy('test_policy')
        assert policy(None) == False
    
    def test_policy_with_complex_logic(self):
        """Test a policy with actual authorization logic."""
        class MockUserAttrs:
            def __init__(self, user_id, roles):
                self.user_id = user_id
                self.roles = roles
        
        class MockObject:
            def __init__(self, owner_id):
                self.owner_id = owner_id
        
        @register_policy('ownership_or_admin')
        def ownership_or_admin(user_attrs, obj=None, action=None):
            if obj is None:
                return False
            # Owner check
            if hasattr(obj, 'owner_id') and obj.owner_id == user_attrs.user_id:
                return True
            # Admin check
            if 'admin' in getattr(user_attrs, 'roles', []):
                return True
            return False
        
        policy = get_policy('ownership_or_admin')
        
        # Test owner access
        user = MockUserAttrs(user_id=1, roles=['user'])
        obj = MockObject(owner_id=1)
        assert policy(user, obj) == True
        
        # Test non-owner without admin
        user = MockUserAttrs(user_id=2, roles=['user'])
        assert policy(user, obj) == False
        
        # Test admin access
        user = MockUserAttrs(user_id=2, roles=['admin'])
        assert policy(user, obj) == True