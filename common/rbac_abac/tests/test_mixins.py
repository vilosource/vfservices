"""
Tests for ABAC model mixins
"""

import pytest
from unittest.mock import Mock, patch
from django.db import models
from common.rbac_abac.mixins import ABACModelMixin
from common.rbac_abac.models import UserAttributes
from common.rbac_abac.registry import register_policy, clear_registry


# Test models
class TestDocument(ABACModelMixin, models.Model):
    """Test model with ABAC support."""
    owner_id = models.IntegerField()
    department = models.CharField(max_length=50)
    
    ABAC_POLICIES = {
        'view': 'test_ownership',
        'edit': 'test_department',
        'delete': 'test_admin_only'
    }
    
    class Meta:
        app_label = 'test'
        managed = False


class TestMinimalModel(ABACModelMixin, models.Model):
    """Test model with minimal ABAC config."""
    name = models.CharField(max_length=50)
    
    class Meta:
        app_label = 'test'
        managed = False


class TestMixinFunctionality:
    
    def setup_method(self):
        """Set up test policies."""
        clear_registry()
        
        @register_policy('test_ownership')
        def test_ownership(user_attrs, obj=None, action=None):
            return obj.owner_id == user_attrs.user_id
        
        @register_policy('test_department')
        def test_department(user_attrs, obj=None, action=None):
            return user_attrs.department == obj.department
        
        @register_policy('test_admin_only')
        def test_admin_only(user_attrs, obj=None, action=None):
            return 'admin' in user_attrs.roles
    
    def test_check_abac_with_valid_policy(self):
        """Test ABAC check with valid policy."""
        doc = TestDocument(owner_id=123, department='IT')
        user = UserAttributes(
            user_id=123,
            username='owner',
            email='owner@test.com',
            department='Sales'
        )
        
        # Owner can view
        assert doc.check_abac(user, 'view') == True
        
        # Non-matching department cannot edit
        assert doc.check_abac(user, 'edit') == False
        
        # Non-admin cannot delete
        assert doc.check_abac(user, 'delete') == False
    
    def test_check_abac_with_admin_role(self):
        """Test ABAC check with admin role."""
        doc = TestDocument(owner_id=999, department='HR')
        admin_user = UserAttributes(
            user_id=123,
            username='admin',
            email='admin@test.com',
            roles=['admin'],
            department='IT'
        )
        
        # Admin can delete
        assert doc.check_abac(admin_user, 'delete') == True
    
    def test_check_abac_with_no_policy(self):
        """Test ABAC check when no policy is defined for action."""
        doc = TestDocument(owner_id=123, department='IT')
        user = UserAttributes(user_id=123, username='user', email='user@test.com')
        
        # No policy for 'create' action
        assert doc.check_abac(user, 'create') == False
    
    def test_check_abac_with_missing_policy(self):
        """Test ABAC check when policy is not in registry."""
        doc = TestDocument(owner_id=123, department='IT')
        doc.ABAC_POLICIES['view'] = 'nonexistent_policy'
        
        user = UserAttributes(user_id=123, username='user', email='user@test.com')
        
        # Should return False when policy not found
        assert doc.check_abac(user, 'view') == False
    
    def test_check_abac_with_invalid_user_attrs(self):
        """Test ABAC check with invalid user attributes."""
        doc = TestDocument(owner_id=123, department='IT')
        
        # Pass dict instead of UserAttributes
        assert doc.check_abac({'user_id': 123}, 'view') == False
        
        # Pass None
        assert doc.check_abac(None, 'view') == False
    
    def test_check_abac_with_policy_error(self):
        """Test ABAC check when policy raises exception."""
        @register_policy('error_policy')
        def error_policy(user_attrs, obj=None, action=None):
            raise ValueError("Policy error")
        
        doc = TestDocument(owner_id=123, department='IT')
        doc.ABAC_POLICIES['view'] = 'error_policy'
        
        user = UserAttributes(user_id=123, username='user', email='user@test.com')
        
        # Should return False on error
        assert doc.check_abac(user, 'view') == False
    
    def test_get_allowed_actions(self):
        """Test getting list of allowed actions."""
        doc = TestDocument(owner_id=123, department='IT')
        user = UserAttributes(
            user_id=123,
            username='owner',
            email='owner@test.com',
            department='IT',
            roles=['user']
        )
        
        allowed = doc.get_allowed_actions(user)
        assert 'view' in allowed  # Owner can view
        assert 'edit' in allowed  # Same department can edit
        assert 'delete' not in allowed  # Not admin
    
    def test_get_allowed_actions_for_admin(self):
        """Test getting allowed actions for admin."""
        doc = TestDocument(owner_id=999, department='HR')
        admin = UserAttributes(
            user_id=123,
            username='admin',
            email='admin@test.com',
            roles=['admin'],
            department='IT'
        )
        
        allowed = doc.get_allowed_actions(admin)
        assert 'delete' in allowed  # Admin can delete
    
    def test_get_required_policies(self):
        """Test getting required policies for model."""
        policies = TestDocument.get_required_policies()
        
        assert policies == {
            'view': 'test_ownership',
            'edit': 'test_department',
            'delete': 'test_admin_only'
        }
    
    def test_default_permission_override(self):
        """Test overriding default permission behavior."""
        class PermissiveModel(ABACModelMixin, models.Model):
            name = models.CharField(max_length=50)
            
            def _default_permission(self, user_attrs, action):
                # Allow all by default (not recommended!)
                return True
            
            class Meta:
                app_label = 'test'
                managed = False
        
        obj = PermissiveModel(name='test')
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        
        # Should allow undefined actions
        assert obj.check_abac(user, 'undefined_action') == True
    
    def test_dynamic_policy_selection(self):
        """Test dynamic policy selection by overriding _get_policy_name."""
        class DynamicModel(ABACModelMixin, models.Model):
            status = models.CharField(max_length=20)
            owner_id = models.IntegerField()
            
            ABAC_POLICIES = {
                'view': 'test_ownership',
                'edit': 'test_ownership'
            }
            
            def _get_policy_name(self, action):
                # Use different policy for archived items
                if self.status == 'archived' and action == 'edit':
                    return 'test_admin_only'
                return super()._get_policy_name(action)
            
            class Meta:
                app_label = 'test'
                managed = False
        
        # Active document
        active_doc = DynamicModel(status='active', owner_id=123)
        owner = UserAttributes(user_id=123, username='owner', email='owner@test.com')
        assert active_doc.check_abac(owner, 'edit') == True
        
        # Archived document - requires admin
        archived_doc = DynamicModel(status='archived', owner_id=123)
        assert archived_doc.check_abac(owner, 'edit') == False
        
        admin = UserAttributes(
            user_id=999,
            username='admin',
            email='admin@test.com',
            roles=['admin']
        )
        assert archived_doc.check_abac(admin, 'edit') == True
    
    def test_model_without_policies(self):
        """Test model without ABAC_POLICIES defined."""
        obj = TestMinimalModel(name='test')
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        
        # Should deny by default
        assert obj.check_abac(user, 'view') == False
        assert obj.get_allowed_actions(user) == []


# Metaclass validation tests removed - feature not implemented
# The ABACModelMetaclass was designed but not integrated into the mixin