"""
Tests for ABAC QuerySet and Manager
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from django.db import models
from django.db.models import Q
from common.rbac_abac.querysets import ABACQuerySet, ABACManager
from common.rbac_abac.models import UserAttributes
from common.rbac_abac.mixins import ABACModelMixin


# Mock Django model for testing
class MockModel(ABACModelMixin, models.Model):
    owner_id = models.IntegerField()
    department = models.CharField(max_length=50)
    group_id = models.IntegerField()
    is_public = models.BooleanField(default=False)
    
    ABAC_POLICIES = {
        'view': 'ownership_check',
        'edit': 'department_match',
        'delete': 'admin_only'
    }
    
    objects = ABACManager()
    
    class Meta:
        app_label = 'test'
        managed = False


class TestABACQuerySet:
    
    @pytest.fixture
    def mock_queryset(self):
        """Create a mock QuerySet."""
        qs = ABACQuerySet(model=MockModel)
        qs._result_cache = None
        return qs
    
    @pytest.fixture
    def user_attrs(self):
        """Create test user attributes."""
        return UserAttributes(
            user_id=123,
            username='testuser',
            email='test@example.com',
            roles=['user'],
            department='IT',
            admin_group_ids=[1, 2, 3]
        )
    
    def test_abac_filter_with_ownership_policy(self, mock_queryset, user_attrs):
        """Test filtering with ownership policy."""
        # Mock the filter method
        with patch.object(mock_queryset, 'filter') as mock_filter:
            mock_queryset.model.ABAC_POLICIES = {'view': 'ownership_check'}
            
            result = mock_queryset.abac_filter(user_attrs, 'view')
            
            # Check that filter was called with ownership Q object
            mock_filter.assert_called_once()
            q_obj = mock_filter.call_args[0][0]
            assert isinstance(q_obj, Q)
            
            # Verify Q object structure
            assert q_obj.children[0] == ('owner_id', 123) or q_obj.children[0] == ('owner__id', 123)
    
    def test_abac_filter_with_department_policy(self, mock_queryset, user_attrs):
        """Test filtering with department policy."""
        with patch.object(mock_queryset, 'filter') as mock_filter:
            mock_queryset.model.ABAC_POLICIES = {'view': 'department_match'}
            
            result = mock_queryset.abac_filter(user_attrs, 'view')
            
            mock_filter.assert_called_once()
            q_obj = mock_filter.call_args[0][0]
            
            # Should filter by department
            assert any(child == ('department', 'IT') for child in q_obj.children)
    
    def test_abac_filter_with_admin_override(self, mock_queryset):
        """Test that admin users see all objects."""
        admin_attrs = UserAttributes(
            user_id=999,
            username='admin',
            email='admin@example.com',
            roles=['admin']
        )
        
        with patch.object(mock_queryset, 'filter') as mock_filter:
            mock_queryset.model.ABAC_POLICIES = {'view': 'ownership_or_admin'}
            
            # Mock the filter to return self (admin sees all)
            mock_filter.return_value = mock_queryset
            
            result = mock_queryset.abac_filter(admin_attrs, 'view')
            
            # Admin should get unfiltered queryset (Q() object)
            q_obj = mock_filter.call_args[0][0]
            # Empty Q() for admin or complex Q with ownership
            assert isinstance(q_obj, Q)
    
    def test_abac_filter_no_policy(self, mock_queryset, user_attrs):
        """Test filtering when no policy is defined."""
        with patch.object(mock_queryset, 'none') as mock_none:
            mock_queryset.model.ABAC_POLICIES = {}
            
            result = mock_queryset.abac_filter(user_attrs, 'undefined_action')
            
            # Should return none() when no policy
            mock_none.assert_called_once()
    
    def test_abac_filter_with_group_membership(self, mock_queryset, user_attrs):
        """Test filtering with group membership policy."""
        with patch.object(mock_queryset, 'filter') as mock_filter:
            mock_queryset.model.ABAC_POLICIES = {'view': 'group_membership'}
            
            result = mock_queryset.abac_filter(user_attrs, 'view')
            
            mock_filter.assert_called_once()
            q_obj = mock_filter.call_args[0][0]
            
            # Should filter by admin_group_ids
            assert any('group_id__in' in str(child) for child in q_obj.children)
    
    def test_abac_filter_with_public_access(self, mock_queryset, user_attrs):
        """Test filtering with public access policy."""
        with patch.object(mock_queryset, 'filter') as mock_filter:
            mock_queryset.model.ABAC_POLICIES = {'view': 'public_access'}
            
            result = mock_queryset.abac_filter(user_attrs, 'view')
            
            mock_filter.assert_called_once()
            q_obj = mock_filter.call_args[0][0]
            
            # Should filter by is_public=True
            assert any(child == ('is_public', True) for child in q_obj.children)
    
    def test_python_filter_fallback(self, mock_queryset, user_attrs):
        """Test fallback to Python-level filtering."""
        # Create mock objects
        obj1 = Mock(pk=1, spec=['pk', 'check_abac'])
        obj1.check_abac.return_value = True
        
        obj2 = Mock(pk=2, spec=['pk', 'check_abac'])
        obj2.check_abac.return_value = False
        
        obj3 = Mock(pk=3, spec=['pk', 'check_abac'])
        obj3.check_abac.return_value = True
        
        # Mock queryset iteration
        mock_queryset.__iter__ = Mock(return_value=iter([obj1, obj2, obj3]))
        mock_queryset.__len__ = Mock(return_value=3)
        mock_queryset.__getitem__ = Mock(side_effect=lambda x: [obj1, obj2, obj3][:x])
        
        with patch.object(mock_queryset, 'filter') as mock_filter:
            mock_filter.return_value = mock_queryset
            
            # Call _python_filter directly
            result = mock_queryset._python_filter(user_attrs, 'view')
            
            # Should filter to include only objects 1 and 3
            mock_filter.assert_called_with(pk__in=[1, 3])
            
            # Verify check_abac was called on each object
            obj1.check_abac.assert_called_with(user_attrs, 'view')
            obj2.check_abac.assert_called_with(user_attrs, 'view')
            obj3.check_abac.assert_called_with(user_attrs, 'view')
    
    def test_custom_model_filter(self, mock_queryset, user_attrs):
        """Test custom filter defined on model."""
        # Add custom filter method to model
        def custom_filter(user_attrs):
            return Q(custom_field='value')
        
        mock_queryset.model._abac_filter_custom_policy = custom_filter
        mock_queryset.model.ABAC_POLICIES = {'view': 'custom_policy'}
        
        with patch.object(mock_queryset, 'filter') as mock_filter:
            result = mock_queryset.abac_filter(user_attrs, 'view')
            
            mock_filter.assert_called_once()
            q_obj = mock_filter.call_args[0][0]
            assert q_obj.children[0] == ('custom_field', 'value')
    
    def test_abac_prefetch(self, mock_queryset, user_attrs):
        """Test queryset prefetching for ABAC."""
        # Mock select_related
        mock_queryset.select_related = Mock(return_value=mock_queryset)
        
        # Add related fields to model
        mock_queryset.model.owner = Mock()
        mock_queryset.model.group = Mock()
        mock_queryset.model.department = Mock()
        
        result = mock_queryset.abac_prefetch(user_attrs, 'view')
        
        # Should prefetch owner, group, department
        mock_queryset.select_related.assert_called_once_with('owner', 'group', 'department')


class TestABACManager:
    
    @pytest.fixture
    def mock_manager(self):
        """Create a mock manager."""
        manager = ABACManager()
        manager.model = MockModel
        manager._db = 'default'
        return manager
    
    def test_get_queryset_returns_abac_queryset(self, mock_manager):
        """Test that manager returns ABACQuerySet."""
        qs = mock_manager.get_queryset()
        assert isinstance(qs, ABACQuerySet)
        assert qs.model == MockModel
    
    def test_abac_filter_convenience_method(self, mock_manager):
        """Test manager's abac_filter method."""
        user_attrs = UserAttributes(
            user_id=123,
            username='test',
            email='test@example.com'
        )
        
        with patch.object(ABACQuerySet, 'abac_filter') as mock_filter:
            mock_manager.abac_filter(user_attrs, 'view')
            mock_filter.assert_called_once_with(user_attrs, 'view')
    
    def test_viewable_by_convenience_method(self, mock_manager):
        """Test viewable_by convenience method."""
        user_attrs = UserAttributes(
            user_id=123,
            username='test',
            email='test@example.com'
        )
        
        with patch.object(mock_manager, 'abac_filter') as mock_filter:
            mock_manager.viewable_by(user_attrs)
            mock_filter.assert_called_once_with(user_attrs, 'view')
    
    def test_editable_by_convenience_method(self, mock_manager):
        """Test editable_by convenience method."""
        user_attrs = UserAttributes(
            user_id=123,
            username='test',
            email='test@example.com'
        )
        
        with patch.object(mock_manager, 'abac_filter') as mock_filter:
            mock_manager.editable_by(user_attrs)
            mock_filter.assert_called_once_with(user_attrs, 'edit')
    
    def test_deletable_by_convenience_method(self, mock_manager):
        """Test deletable_by convenience method."""
        user_attrs = UserAttributes(
            user_id=123,
            username='test',
            email='test@example.com'
        )
        
        with patch.object(mock_manager, 'abac_filter') as mock_filter:
            mock_manager.deletable_by(user_attrs)
            mock_filter.assert_called_once_with(user_attrs, 'delete')


class TestQuerySetFilters:
    """Test specific filter implementations."""
    
    @pytest.fixture
    def queryset(self):
        """Create test queryset."""
        return ABACQuerySet(model=MockModel)
    
    def test_ownership_filter(self, queryset):
        """Test ownership filter Q object generation."""
        user_attrs = UserAttributes(user_id=42, username='test', email='test@test.com')
        
        q = queryset._ownership_filter(user_attrs)
        
        # Should create OR condition for owner_id and owner__id
        assert isinstance(q, Q)
        assert len(q.children) == 2
        assert ('owner_id', 42) in q.children or ('owner__id', 42) in q.children
    
    def test_department_filter_with_department(self, queryset):
        """Test department filter when user has department."""
        user_attrs = UserAttributes(
            user_id=1,
            username='test',
            email='test@test.com',
            department='Engineering'
        )
        
        q = queryset._department_filter(user_attrs)
        
        assert isinstance(q, Q)
        assert ('department', 'Engineering') in q.children
    
    def test_department_filter_without_department(self, queryset):
        """Test department filter when user has no department."""
        user_attrs = UserAttributes(
            user_id=1,
            username='test',
            email='test@test.com',
            department=None
        )
        
        q = queryset._department_filter(user_attrs)
        
        # Should return empty filter (no access)
        assert ('pk__in', []) in q.children
    
    def test_department_filter_admin_override(self, queryset):
        """Test department filter with admin role."""
        user_attrs = UserAttributes(
            user_id=1,
            username='admin',
            email='admin@test.com',
            roles=['admin']
        )
        
        q = queryset._department_filter(user_attrs)
        
        # Admin should get empty Q (all access)
        assert len(q.children) == 0
    
    def test_group_membership_filter(self, queryset):
        """Test group membership filter."""
        user_attrs = UserAttributes(
            user_id=1,
            username='test',
            email='test@test.com',
            admin_group_ids=[10, 20, 30]
        )
        
        # Add group_id field to model
        queryset.model.group_id = Mock()
        
        q = queryset._group_membership_filter(user_attrs)
        
        assert isinstance(q, Q)
        # Should filter by group_id in admin_group_ids
        assert any('group_id__in' in str(child) for child in q.children)