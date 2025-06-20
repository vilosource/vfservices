"""
Tests for DRF permission classes
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.permissions import BasePermission
from django.contrib.auth.models import User
from common.rbac_abac.permissions import (
    ABACPermission, RoleRequired, CombinedPermission, ServicePermission
)
from common.rbac_abac.models import UserAttributes


class TestABACPermission:
    
    @pytest.fixture
    def mock_request(self):
        """Create mock DRF request."""
        request = Mock(spec=Request)
        request.user = Mock(spec=User)
        request.user.id = 123
        request.user.is_authenticated = True
        request.method = 'GET'
        return request
    
    @pytest.fixture
    def mock_view(self):
        """Create mock view."""
        view = Mock(spec=APIView)
        view.service_name = 'test_service'
        view.action = None
        return view
    
    @pytest.fixture
    def mock_object(self):
        """Create mock object with ABAC support."""
        obj = Mock()
        obj.check_abac = Mock(return_value=True)
        return obj
    
    @pytest.fixture
    def user_attrs(self):
        """Create test user attributes."""
        return UserAttributes(
            user_id=123,
            username='testuser',
            email='test@example.com',
            roles=['user']
        )
    
    def test_has_permission_authenticated(self, mock_request, mock_view):
        """Test has_permission for authenticated user."""
        permission = ABACPermission()
        assert permission.has_permission(mock_request, mock_view) == True
    
    def test_has_permission_unauthenticated(self, mock_request, mock_view):
        """Test has_permission for unauthenticated user."""
        mock_request.user.is_authenticated = False
        permission = ABACPermission()
        assert permission.has_permission(mock_request, mock_view) == False
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_has_object_permission_allowed(self, mock_get_attrs, mock_request, 
                                         mock_view, mock_object, user_attrs):
        """Test has_object_permission when access is allowed."""
        mock_get_attrs.return_value = user_attrs
        
        permission = ABACPermission()
        result = permission.has_object_permission(mock_request, mock_view, mock_object)
        
        assert result == True
        mock_get_attrs.assert_called_once_with(123, 'test_service')
        mock_object.check_abac.assert_called_once_with(user_attrs, 'view')
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_has_object_permission_denied(self, mock_get_attrs, mock_request,
                                        mock_view, mock_object, user_attrs):
        """Test has_object_permission when access is denied."""
        mock_get_attrs.return_value = user_attrs
        mock_object.check_abac.return_value = False
        
        permission = ABACPermission()
        result = permission.has_object_permission(mock_request, mock_view, mock_object)
        
        assert result == False
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_has_object_permission_no_service_name(self, mock_get_attrs, mock_request,
                                                  mock_view, mock_object):
        """Test has_object_permission when service name is missing."""
        mock_view.service_name = None
        
        permission = ABACPermission()
        result = permission.has_object_permission(mock_request, mock_view, mock_object)
        
        assert result == False
        mock_get_attrs.assert_not_called()
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_has_object_permission_no_user_attrs(self, mock_get_attrs, mock_request,
                                                mock_view, mock_object):
        """Test has_object_permission when user attributes not found."""
        mock_get_attrs.return_value = None
        
        permission = ABACPermission()
        result = permission.has_object_permission(mock_request, mock_view, mock_object)
        
        assert result == False
    
    def test_has_object_permission_no_abac_support(self, mock_request, mock_view):
        """Test has_object_permission for object without ABAC support."""
        obj = Mock(spec=[])  # No check_abac method - empty spec
        
        permission = ABACPermission()
        with patch('common.rbac_abac.permissions.get_user_attributes') as mock_get_attrs:
            mock_get_attrs.return_value = Mock()
            result = permission.has_object_permission(mock_request, mock_view, obj)
        
        assert result == True  # Allow if no ABAC configured
    
    def test_get_service_name_from_view(self, mock_view):
        """Test getting service name from view attribute."""
        permission = ABACPermission()
        assert permission._get_service_name(mock_view) == 'test_service'
    
    def test_get_service_name_from_method(self):
        """Test getting service name from view method."""
        view = Mock(spec=['get_service_name'])
        view.get_service_name = Mock(return_value='method_service')
        
        permission = ABACPermission()
        assert permission._get_service_name(view) == 'method_service'
    
    @patch('django.conf.settings')
    def test_get_service_name_from_settings(self, mock_settings):
        """Test getting service name from Django settings."""
        mock_settings.SERVICE_NAME = 'settings_service'
        
        view = Mock(spec=[])  # No service_name or get_service_name
        
        permission = ABACPermission()
        assert permission._get_service_name(view) == 'settings_service'
    
    def test_get_action_from_view(self, mock_request, mock_view):
        """Test getting action from view.action."""
        mock_view.action = 'custom_action'
        
        permission = ABACPermission()
        assert permission._get_action(mock_request, mock_view) == 'custom_action'
    
    def test_get_action_from_method_mapping(self, mock_request, mock_view):
        """Test getting action from HTTP method."""
        test_cases = [
            ('GET', 'view'),
            ('POST', 'create'),
            ('PUT', 'edit'),
            ('PATCH', 'edit'),
            ('DELETE', 'delete'),
            ('HEAD', 'view'),
            ('OPTIONS', 'view'),
        ]
        
        permission = ABACPermission()
        for method, expected_action in test_cases:
            mock_request.method = method
            assert permission._get_action(mock_request, mock_view) == expected_action
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_user_attrs_caching(self, mock_get_attrs, mock_request, mock_view, 
                               mock_object, user_attrs):
        """Test that user attributes are cached on request."""
        mock_get_attrs.return_value = user_attrs
        
        permission = ABACPermission()
        
        # First call
        permission.has_object_permission(mock_request, mock_view, mock_object)
        
        # Second call with same request
        permission.has_object_permission(mock_request, mock_view, mock_object)
        
        # Should only fetch from Redis once due to caching
        mock_get_attrs.assert_called_once()


class TestRoleRequired:
    
    @pytest.fixture
    def mock_request(self):
        """Create mock DRF request."""
        request = Mock(spec=Request)
        request.user = Mock(spec=User)
        request.user.id = 123
        request.user.is_authenticated = True
        return request
    
    @pytest.fixture
    def mock_view(self):
        """Create mock view."""
        view = Mock(spec=APIView)
        view.service_name = 'test_service'
        return view
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_single_role_allowed(self, mock_get_attrs, mock_request, mock_view):
        """Test access with required role."""
        user_attrs = UserAttributes(
            user_id=123,
            username='admin',
            email='admin@test.com',
            roles=['admin', 'user']
        )
        mock_get_attrs.return_value = user_attrs
        
        permission = RoleRequired('admin')
        assert permission.has_permission(mock_request, mock_view) == True
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_single_role_denied(self, mock_get_attrs, mock_request, mock_view):
        """Test denial when missing required role."""
        user_attrs = UserAttributes(
            user_id=123,
            username='user',
            email='user@test.com',
            roles=['user']
        )
        mock_get_attrs.return_value = user_attrs
        
        permission = RoleRequired('admin')
        assert permission.has_permission(mock_request, mock_view) == False
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_multiple_roles_any_match(self, mock_get_attrs, mock_request, mock_view):
        """Test access when user has any of multiple required roles."""
        user_attrs = UserAttributes(
            user_id=123,
            username='editor',
            email='editor@test.com',
            roles=['editor', 'user']
        )
        mock_get_attrs.return_value = user_attrs
        
        permission = RoleRequired('admin', 'editor', 'moderator')
        assert permission.has_permission(mock_request, mock_view) == True
    
    def test_unauthenticated_user(self, mock_request, mock_view):
        """Test denial for unauthenticated user."""
        mock_request.user.is_authenticated = False
        
        permission = RoleRequired('any_role')
        assert permission.has_permission(mock_request, mock_view) == False
    
    @patch('common.rbac_abac.permissions.get_user_attributes')
    def test_no_user_attributes(self, mock_get_attrs, mock_request, mock_view):
        """Test denial when user attributes not found."""
        mock_get_attrs.return_value = None
        
        permission = RoleRequired('admin')
        assert permission.has_permission(mock_request, mock_view) == False


class TestServicePermission:
    
    @pytest.fixture
    def mock_view_with_queryset(self):
        """Create mock view with queryset."""
        view = Mock()
        view.service_name = None
        view.queryset = Mock()
        view.queryset.model = Mock()
        view.queryset.model._meta = Mock()
        view.queryset.model._meta.app_label = 'billing_api'
        return view
    
    def test_auto_detect_from_app_label(self, mock_view_with_queryset):
        """Test auto-detection of service name from app label."""
        permission = ServicePermission()
        service_name = permission._get_service_name(mock_view_with_queryset)
        assert service_name == 'billing-api'
    
    def test_auto_detect_from_module(self):
        """Test auto-detection of service name from module."""
        view = Mock()
        view.service_name = None
        view.queryset = None
        view.__module__ = 'billing_api.views.invoice'
        
        permission = ServicePermission()
        service_name = permission._get_service_name(view)
        assert service_name == 'billing-api'
    
    def test_fallback_to_parent_logic(self):
        """Test fallback to parent class logic."""
        view = Mock()
        view.service_name = 'explicit_service'
        view.queryset = None
        
        permission = ServicePermission()
        service_name = permission._get_service_name(view)
        assert service_name == 'explicit_service'


class TestCombinedPermission:
    
    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        return Mock(spec=Request)
    
    @pytest.fixture
    def mock_view(self):
        """Create mock view."""
        return Mock(spec=APIView)
    
    @pytest.fixture
    def mock_object(self):
        """Create mock object."""
        return Mock()
    
    def test_and_combination_both_pass(self, mock_request, mock_view):
        """Test AND combination when both permissions pass."""
        perm1 = Mock(spec=BasePermission)
        perm1.has_permission.return_value = True
        
        perm2 = Mock(spec=BasePermission)
        perm2.has_permission.return_value = True
        
        # Create AND expression
        expr = Mock()
        expr.op = '&'
        expr.left = perm1
        expr.right = perm2
        
        combined = CombinedPermission(expr)
        assert combined.has_permission(mock_request, mock_view) == True
        
        perm1.has_permission.assert_called_once()
        perm2.has_permission.assert_called_once()
    
    def test_and_combination_first_fails(self, mock_request, mock_view):
        """Test AND combination when first permission fails."""
        perm1 = Mock(spec=BasePermission)
        perm1.has_permission.return_value = False
        
        perm2 = Mock(spec=BasePermission)
        perm2.has_permission.return_value = True
        
        expr = Mock()
        expr.op = '&'
        expr.left = perm1
        expr.right = perm2
        
        combined = CombinedPermission(expr)
        assert combined.has_permission(mock_request, mock_view) == False
        
        perm1.has_permission.assert_called_once()
        perm2.has_permission.assert_not_called()  # Short-circuit
    
    def test_or_combination_first_passes(self, mock_request, mock_view):
        """Test OR combination when first permission passes."""
        perm1 = Mock(spec=BasePermission)
        perm1.has_permission.return_value = True
        
        perm2 = Mock(spec=BasePermission)
        perm2.has_permission.return_value = False
        
        expr = Mock()
        expr.op = '|'
        expr.left = perm1
        expr.right = perm2
        
        combined = CombinedPermission(expr)
        assert combined.has_permission(mock_request, mock_view) == True
        
        perm1.has_permission.assert_called_once()
        perm2.has_permission.assert_not_called()  # Short-circuit
    
    def test_or_combination_both_fail(self, mock_request, mock_view):
        """Test OR combination when both permissions fail."""
        perm1 = Mock(spec=BasePermission)
        perm1.has_permission.return_value = False
        
        perm2 = Mock(spec=BasePermission)
        perm2.has_permission.return_value = False
        
        expr = Mock()
        expr.op = '|'
        expr.left = perm1
        expr.right = perm2
        
        combined = CombinedPermission(expr)
        assert combined.has_permission(mock_request, mock_view) == False
        
        perm1.has_permission.assert_called_once()
        perm2.has_permission.assert_called_once()
    
    def test_object_permission(self, mock_request, mock_view, mock_object):
        """Test combined permission for object-level checks."""
        perm1 = Mock(spec=BasePermission)
        perm1.has_object_permission.return_value = True
        
        perm2 = Mock(spec=BasePermission)
        perm2.has_object_permission.return_value = True
        
        expr = Mock()
        expr.op = '&'
        expr.left = perm1
        expr.right = perm2
        
        combined = CombinedPermission(expr)
        assert combined.has_object_permission(mock_request, mock_view, mock_object) == True
        
        perm1.has_object_permission.assert_called_once_with(mock_request, mock_view, mock_object)
        perm2.has_object_permission.assert_called_once_with(mock_request, mock_view, mock_object)