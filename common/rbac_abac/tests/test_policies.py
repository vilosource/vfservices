"""
Tests for default ABAC policies
"""

import pytest
from unittest.mock import Mock
from common.rbac_abac.models import UserAttributes
from common.rbac_abac.policies import (
    ownership_check, ownership_or_admin, department_match,
    department_match_or_admin, group_membership, public_access,
    authenticated_only, admin_only, service_admin, owner_or_group_admin,
    customer_access, document_access, read_only, deny_all,
    create_composite_policy
)
from common.rbac_abac.registry import clear_registry, get_policy


class TestOwnershipPolicies:
    
    def test_ownership_check_with_owner_id(self):
        """Test ownership check with owner_id field."""
        user = UserAttributes(user_id=123, username='owner', email='owner@test.com')
        obj = Mock(owner_id=123)
        
        assert ownership_check(user, obj) == True
        
        # Different user
        other_user = UserAttributes(user_id=456, username='other', email='other@test.com')
        assert ownership_check(other_user, obj) == False
    
    def test_ownership_check_with_owner_object(self):
        """Test ownership check with owner relationship."""
        user = UserAttributes(user_id=123, username='owner', email='owner@test.com')
        obj = Mock()
        obj.owner = Mock(id=123)
        
        assert ownership_check(user, obj) == True
    
    def test_ownership_check_no_owner(self):
        """Test ownership check when object has no owner field."""
        user = UserAttributes(user_id=123, username='user', email='user@test.com')
        obj = Mock(spec=[])  # No owner attributes
        
        assert ownership_check(user, obj) == False
    
    def test_ownership_or_admin(self):
        """Test ownership or admin policy."""
        owner = UserAttributes(user_id=123, username='owner', email='owner@test.com')
        admin = UserAttributes(user_id=456, username='admin', email='admin@test.com', 
                             roles=['admin'])
        other = UserAttributes(user_id=789, username='other', email='other@test.com')
        
        obj = Mock(owner_id=123)
        
        assert ownership_or_admin(owner, obj) == True
        assert ownership_or_admin(admin, obj) == True
        assert ownership_or_admin(other, obj) == False
    
    def test_ownership_or_admin_service_specific(self):
        """Test service-specific admin role."""
        user = UserAttributes(user_id=456, username='billing_admin', 
                            email='admin@test.com', roles=['billing_api_admin'])
        
        obj = Mock(owner_id=123)
        obj._meta = Mock(app_label='billing_api')
        
        assert ownership_or_admin(user, obj) == True


class TestDepartmentPolicies:
    
    def test_department_match(self):
        """Test department matching policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com',
                            department='Engineering')
        obj = Mock(department='Engineering')
        
        assert department_match(user, obj) == True
        
        # Different department
        obj.department = 'Sales'
        assert department_match(user, obj) == False
    
    def test_department_match_no_user_department(self):
        """Test when user has no department."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        obj = Mock(department='Engineering')
        
        assert department_match(user, obj) == False
    
    def test_department_match_or_admin(self):
        """Test department match or admin policy."""
        eng_user = UserAttributes(user_id=1, username='eng', email='eng@test.com',
                                department='Engineering')
        admin = UserAttributes(user_id=2, username='admin', email='admin@test.com',
                             roles=['admin'])
        
        obj = Mock(department='Engineering')
        
        assert department_match_or_admin(eng_user, obj) == True
        assert department_match_or_admin(admin, obj) == True
        
        # Different department, not admin
        sales_user = UserAttributes(user_id=3, username='sales', email='sales@test.com',
                                  department='Sales')
        assert department_match_or_admin(sales_user, obj) == False


class TestGroupPolicies:
    
    def test_group_membership_admin(self):
        """Test group membership for group admin."""
        user = UserAttributes(user_id=1, username='admin', email='admin@test.com',
                            admin_group_ids=[10, 20, 30])
        obj = Mock(group_id=20)
        
        assert group_membership(user, obj) == True
        
        # Not admin of this group
        obj.group_id = 40
        assert group_membership(user, obj) == False
    
    def test_group_membership_with_group_object(self):
        """Test group membership with group relationship."""
        user = UserAttributes(user_id=1, username='admin', email='admin@test.com',
                            admin_group_ids=[10, 20])
        obj = Mock()
        obj.group = Mock(id=10)
        
        assert group_membership(user, obj) == True
    
    def test_owner_or_group_admin(self):
        """Test owner or group admin policy."""
        user = UserAttributes(user_id=123, username='user', email='user@test.com',
                            admin_group_ids=[10, 20])
        
        # User owns object
        obj1 = Mock(owner_id=123, group_id=30)
        assert owner_or_group_admin(user, obj1) == True
        
        # User is admin of object's group
        obj2 = Mock(owner_id=456, group_id=10)
        assert owner_or_group_admin(user, obj2) == True
        
        # Neither owner nor group admin
        obj3 = Mock(owner_id=456, group_id=30)
        assert owner_or_group_admin(user, obj3) == False


class TestAccessPolicies:
    
    def test_public_access(self):
        """Test public access policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        
        # Various public field names
        obj1 = Mock(is_public=True)
        assert public_access(user, obj1) == True
        
        obj2 = Mock(public=True)
        assert public_access(user, obj2) == True
        
        obj3 = Mock(visibility='public')
        assert public_access(user, obj3) == True
        
        obj4 = Mock(access_level='public')
        assert public_access(user, obj4) == True
        
        # Not public
        obj5 = Mock(is_public=False)
        assert public_access(user, obj5) == False
    
    def test_authenticated_only(self):
        """Test authenticated only policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        assert authenticated_only(user) == True
        
        # No user attributes
        assert authenticated_only(None) == False
    
    def test_admin_only(self):
        """Test admin only policy."""
        admin = UserAttributes(user_id=1, username='admin', email='admin@test.com',
                             roles=['admin'])
        superuser = UserAttributes(user_id=2, username='super', email='super@test.com',
                                 roles=['superuser'])
        regular = UserAttributes(user_id=3, username='user', email='user@test.com',
                               roles=['user'])
        
        assert admin_only(admin) == True
        assert admin_only(superuser) == True
        assert admin_only(regular) == False
    
    def test_service_admin(self):
        """Test service admin policy."""
        global_admin = UserAttributes(user_id=1, username='admin', email='admin@test.com',
                                    roles=['admin'])
        service_admin = UserAttributes(user_id=2, username='billing_admin', 
                                     email='billing@test.com', roles=['billing_api_admin'])
        regular = UserAttributes(user_id=3, username='user', email='user@test.com')
        
        obj = Mock()
        obj._meta = Mock(app_label='billing_api')
        
        assert service_admin(global_admin, obj) == True
        assert service_admin(service_admin, obj) == True
        assert service_admin(regular, obj) == False


class TestCustomerAndDocumentPolicies:
    
    def test_customer_access(self):
        """Test customer access policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com',
                            customer_ids=[100, 200, 300])
        
        # Direct customer_id
        obj1 = Mock(customer_id=200)
        assert customer_access(user, obj1) == True
        
        # Customer relationship
        obj2 = Mock()
        obj2.customer = Mock(id=100)
        assert customer_access(user, obj2) == True
        
        # No access
        obj3 = Mock(customer_id=400)
        assert customer_access(user, obj3) == False
    
    def test_document_access(self):
        """Test document access policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com',
                            assigned_doc_ids=[10, 20, 30])
        
        obj1 = Mock(id=20)
        assert document_access(user, obj1) == True
        
        obj2 = Mock(id=40)
        assert document_access(user, obj2) == False


class TestUtilityPolicies:
    
    def test_read_only(self):
        """Test read-only policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        obj = Mock()
        
        assert read_only(user, obj, 'view') == True
        assert read_only(user, obj, 'list') == True
        assert read_only(user, obj, 'retrieve') == True
        assert read_only(user, obj, 'edit') == False
        assert read_only(user, obj, 'delete') == False
    
    def test_deny_all(self):
        """Test deny all policy."""
        user = UserAttributes(user_id=1, username='user', email='user@test.com',
                            roles=['admin'])
        obj = Mock()
        
        assert deny_all(user, obj, 'view') == False
        assert deny_all(user, obj, 'edit') == False
        assert deny_all(user, obj, 'anything') == False


class TestCompositePolicies:
    
    def setup_method(self):
        """Clear registry before each test."""
        clear_registry()
    
    def test_create_composite_policy_and(self):
        """Test creating composite policy with AND logic."""
        # Register test policies
        @pytest.fixture(autouse=True)
        def register_test_policies():
            from common.rbac_abac.registry import register_policy
            
            @register_policy('always_true')
            def always_true(user_attrs, obj=None, action=None):
                return True
            
            @register_policy('always_false')
            def always_false(user_attrs, obj=None, action=None):
                return False
        
        # Import after registration
        from common.rbac_abac.policies import create_composite_policy
        
        # Create AND composite
        create_composite_policy('test_and', 'always_true', 'always_false', require_all=True)
        
        policy = get_policy('test_and')
        assert policy is not None
        
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        assert policy(user) == False  # One is false, so AND is false
    
    def test_create_composite_policy_or(self):
        """Test creating composite policy with OR logic."""
        # Register test policies
        from common.rbac_abac.registry import register_policy
        
        @register_policy('check_a')
        def check_a(user_attrs, obj=None, action=None):
            return hasattr(obj, 'has_a') and obj.has_a
        
        @register_policy('check_b')
        def check_b(user_attrs, obj=None, action=None):
            return hasattr(obj, 'has_b') and obj.has_b
        
        # Import after registration
        from common.rbac_abac.policies import create_composite_policy
        
        # Create OR composite
        create_composite_policy('test_or', 'check_a', 'check_b', require_all=False)
        
        policy = get_policy('test_or')
        user = UserAttributes(user_id=1, username='user', email='user@test.com')
        
        obj1 = Mock(has_a=True, has_b=False)
        assert policy(user, obj1) == True  # One is true
        
        obj2 = Mock(has_a=False, has_b=False)
        assert policy(user, obj2) == False  # Both false