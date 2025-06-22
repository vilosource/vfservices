import json
import requests
import logging
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from common.rbac_abac import get_user_attributes

logger = logging.getLogger(__name__)

# Demo users with their credentials and expected attributes
DEMO_USERS = {
    'alice': {
        'username': 'alice',
        'password': 'alice123',
        'name': 'Alice (Senior Manager)',
        'display_role': 'Senior Manager',
        'department': 'Management',
        'description': 'Billing admin, inventory manager, can approve high-value transactions',
        'expected_roles': {
            'billing_api': ['billing_admin'],
            'inventory_api': ['inventory_manager'],
            'identity_provider': ['customer_manager']
        },
        'expected_attrs': {
            'department': 'Management',
            'customer_ids': [100, 200, 300, 400, 500],
            'warehouse_ids': [1, 2],
            'invoice_limit': 50000,
            'max_refund_amount': 10000,
            'can_export_data': True
        }
    },
    'bob': {
        'username': 'bob',
        'password': 'bob123',
        'name': 'Bob (Billing Specialist)',
        'display_role': 'Billing Specialist',
        'department': 'Finance',
        'description': 'Can create invoices, process payments, view inventory',
        'expected_roles': {
            'billing_api': ['invoice_manager', 'payment_processor', 'invoice_sender'],
            'inventory_api': ['stock_viewer']
        },
        'expected_attrs': {
            'department': 'Finance',
            'customer_ids': [100, 200, 300],
            'invoice_limit': 5000,
            'payment_methods': ['credit_card', 'bank_transfer'],
            'max_refund_amount': 1000
        }
    },
    'charlie': {
        'username': 'charlie',
        'password': 'charlie123',
        'name': 'Charlie (Cloud Infrastructure Manager)',
        'display_role': 'Cloud Infrastructure Manager',
        'department': 'Operations',
        'description': 'Manages warehouse 1 (us-east-1) resources',
        'expected_roles': {
            'inventory_api': ['warehouse_manager', 'stock_adjuster', 'movement_approver', 'count_supervisor']
        },
        'expected_attrs': {
            'department': 'Operations',
            'warehouse_ids': [1],
            'product_categories': ['compute', 'storage'],
            'max_adjustment_value': 5000,
            'movement_types': ['migration', 'decommission', 'reallocation'],
            'can_export_data': False
        }
    },
    'david': {
        'username': 'david',
        'password': 'david123',
        'name': 'David (Customer Service Rep)',
        'display_role': 'Customer Service Representative',
        'department': 'Support',
        'description': 'Read-only access to customer 100 data',
        'expected_roles': {
            'billing_api': ['invoice_viewer', 'payment_viewer'],
            'inventory_api': ['product_viewer', 'stock_viewer']
        },
        'expected_attrs': {
            'department': 'Support',
            'customer_ids': [100],
            'warehouse_ids': [],
            'invoice_limit': 0,
            'can_export_data': False
        }
    }
}

# API endpoints for each service - including RBAC test endpoints
API_ENDPOINTS = {
    'identity': {
        'base_url': 'http://identity-provider:8000',
        'endpoints': [
            {'name': 'Login', 'path': '/api/login/', 'method': 'POST', 'requires_auth': False},
            {'name': 'Status', 'path': '/api/status/', 'method': 'GET', 'requires_auth': True},
            {'name': 'Profile', 'path': '/api/profile/', 'method': 'GET', 'requires_auth': True},
            {'name': 'Service Registration', 'path': '/api/services/register/', 'method': 'POST', 'requires_auth': False},
        ]
    },
    'billing': {
        'base_url': 'http://billing-api:8000',
        'endpoints': [
            {'name': 'Home', 'path': '/', 'method': 'GET', 'requires_auth': False},
            {'name': 'Health Check', 'path': '/health/', 'method': 'GET', 'requires_auth': False},
            {'name': 'Test RBAC', 'path': '/test-rbac/', 'method': 'GET', 'requires_auth': True},
            {'name': 'Basic Private', 'path': '/private/', 'method': 'GET', 'requires_auth': True},
            {'name': 'Billing Admin Only', 'path': '/billing-admin/', 'method': 'GET', 'requires_auth': True, 'required_role': 'billing_admin'},
            {'name': 'Customer Manager Only', 'path': '/customer-manager/', 'method': 'GET', 'requires_auth': True, 'required_role': 'customer_manager'},
            {'name': 'Invoice Manager Only', 'path': '/invoice-manager/', 'method': 'GET', 'requires_auth': True, 'required_role': 'invoice_manager'},
        ]
    },
    'inventory': {
        'base_url': 'http://inventory-api:8000',
        'endpoints': [
            {'name': 'Health Check', 'path': '/health/', 'method': 'GET', 'requires_auth': False},
            {'name': 'Test RBAC', 'path': '/test-rbac/', 'method': 'GET', 'requires_auth': True},
            {'name': 'Basic Private', 'path': '/private/', 'method': 'GET', 'requires_auth': True},
            {'name': 'Inventory Manager Only', 'path': '/inventory-manager/', 'method': 'GET', 'requires_auth': True, 'required_role': 'inventory_manager'},
        ]
    }
}


def dashboard(request):
    """Main demo dashboard"""
    # Check setup status
    setup_status = {
        'services_registered': 0,
        'users_created': 0,
        'roles_assigned': 0,
        'is_complete': False
    }
    
    try:
        from identity_app.models import Service, UserRole
        
        # Count registered services
        setup_status['services_registered'] = Service.objects.filter(is_active=True).count()
        
        # Count demo users created
        for username in DEMO_USERS.keys():
            if User.objects.filter(username=username).exists():
                setup_status['users_created'] += 1
        
        # Count roles assigned
        demo_usernames = list(DEMO_USERS.keys())
        setup_status['roles_assigned'] = UserRole.objects.filter(
            user__username__in=demo_usernames
        ).count()
        
        # Check if setup is complete
        expected_services = 3  # billing_api, inventory_api, identity_provider
        expected_users = len(DEMO_USERS)
        setup_status['is_complete'] = (
            setup_status['services_registered'] >= expected_services and
            setup_status['users_created'] == expected_users and
            setup_status['roles_assigned'] > 0
        )
        
    except:
        pass
    
    context = {
        'demo_users': DEMO_USERS,
        'current_user': request.session.get('demo_user', None),
        'api_endpoints': API_ENDPOINTS,
        'setup_status': setup_status
    }
    return render(request, 'demo/dashboard.html', context)


def rbac_dashboard(request):
    """RBAC-ABAC demonstration dashboard"""
    current_user = request.session.get('demo_user', None)
    current_user_data = None
    actual_permissions = {}
    
    if current_user:
        user_data = DEMO_USERS.get(current_user, {})
        # Try to get actual user from database
        try:
            user_obj = User.objects.get(username=current_user)
            # Get actual permissions from Redis for each service
            for service in ['billing_api', 'inventory_api', 'identity_provider']:
                try:
                    attrs = get_user_attributes(user_obj.id, service)
                    actual_permissions[service] = {
                        'roles': attrs.roles if attrs else [],
                        'attributes': attrs.__dict__ if attrs else {}
                    }
                except:
                    actual_permissions[service] = {'roles': [], 'attributes': {}}
            
            current_user_data = user_data.copy()
            current_user_data['actual_permissions'] = actual_permissions
        except User.DoesNotExist:
            current_user_data = user_data
    
    context = {
        'demo_users': DEMO_USERS,
        'current_user': current_user,
        'current_user_data': current_user_data,
    }
    return render(request, 'demo/rbac_dashboard.html', context)


def api_explorer(request):
    """Interactive API testing interface"""
    # Try to get dynamic endpoint information from services
    api_endpoints = API_ENDPOINTS.copy()
    
    # Get current user's roles for display
    current_user_roles = {}
    current_user = request.session.get('demo_user', None)
    
    # Debug logging
    logger.debug(f"API Explorer - Current user: {current_user}")
    logger.debug(f"API Explorer - Demo users available: {list(DEMO_USERS.keys())}")
    
    if current_user:
        try:
            user = User.objects.get(username=current_user)
            from identity_app.models import UserRole
            
            # Get roles by service
            user_roles = UserRole.objects.filter(user=user).select_related('role__service')
            for ur in user_roles:
                service = ur.role.service.name
                if service not in current_user_roles:
                    current_user_roles[service] = []
                current_user_roles[service].append(ur.role.name)
        except Exception as e:
            logger.error(f"Error getting user roles: {e}")
            pass
    
    context = {
        'api_endpoints': api_endpoints,
        'current_user': current_user,
        'current_user_roles': current_user_roles,
        'access_token': request.session.get('demo_access_token', None),
        'demo_users': DEMO_USERS,  # Add this for the user switcher
    }
    return render(request, 'demo/api_explorer.html', context)


def permission_matrix(request):
    """Visual permission matrix"""
    # Get actual roles from database
    all_roles = {}
    user_permissions = {}
    
    try:
        # Import here to avoid circular imports
        from identity_app.models import Service, Role, UserRole
        
        # Get all services and their roles
        for service in Service.objects.filter(is_active=True):
            service_roles = Role.objects.filter(service=service).values_list('name', flat=True)
            all_roles[service.name] = list(service_roles)
        
        # Get each demo user's actual roles
        for username in DEMO_USERS.keys():
            try:
                user = User.objects.get(username=username)
                user_permissions[username] = {}
                
                for service in Service.objects.filter(is_active=True):
                    user_roles = UserRole.objects.filter(
                        user=user, 
                        role__service=service
                    ).values_list('role__name', flat=True)
                    user_permissions[username][service.name] = list(user_roles)
                    
            except User.DoesNotExist:
                user_permissions[username] = {}
                
    except:
        # Fallback to expected permissions if models not available
        for username, user_data in DEMO_USERS.items():
            user_permissions[username] = user_data.get('expected_roles', {})
            
        # Collect all unique roles
        for user_data in DEMO_USERS.values():
            for service, roles in user_data.get('expected_roles', {}).items():
                if service not in all_roles:
                    all_roles[service] = []
                all_roles[service].extend(roles)
        
        # Remove duplicates
        for service in all_roles:
            all_roles[service] = list(set(all_roles[service]))
    
    # Calculate total roles
    total_roles = sum(len(roles) for roles in all_roles.values())
    
    context = {
        'demo_users': DEMO_USERS,
        'all_roles': all_roles,
        'user_permissions': user_permissions,
        'current_user': request.session.get('demo_user', None),
        'total_roles': total_roles,
    }
    return render(request, 'demo/permission_matrix.html', context)


def playground(request):
    """Interactive access scenarios"""
    # Set default demo user if none is set
    if 'demo_user' not in request.session:
        request.session['demo_user'] = 'alice'
    
    scenarios = [
        {
            'id': 'super_admin_access',
            'title': 'SuperAdmin Full Access',
            'description': 'Alice can access all services without restrictions',
            'user': 'alice',
            'steps': [
                'Login as Alice',
                'Access billing private endpoint',
                'Access inventory private endpoint',
                'View all customer data',
            ]
        },
        {
            'id': 'billing_specialist_access',
            'title': 'Billing Specialist Access',
            'description': 'Bob can manage invoices and payments, view inventory',
            'user': 'bob',
            'steps': [
                'Login as Bob',
                'Access billing endpoints (invoice, payment)',
                'View inventory data (read-only)',
                'Create and send invoices',
                'Process payments up to limit',
            ]
        },
        {
            'id': 'warehouse_manager_access',
            'title': 'Warehouse Manager Access',
            'description': 'Charlie manages warehouse 1 (us-east-1) resources',
            'user': 'charlie',
            'steps': [
                'Login as Charlie',
                'Access inventory data and stock information',
                'Manage warehouse 1 resources',
                'Adjust stock levels and approve movements',
                'Cannot access billing role-specific endpoints',
            ]
        },
        {
            'id': 'readonly_access',
            'title': 'Read-Only Access Pattern',
            'description': 'David has read-only access across services',
            'user': 'david',
            'steps': [
                'Login as David',
                'Read billing data',
                'Read inventory data',
                'Try to modify data (should fail)',
            ]
        }
    ]
    
    context = {
        'scenarios': scenarios,
        'current_user': request.session.get('demo_user', None),
        'demo_users': DEMO_USERS,
    }
    return render(request, 'demo/playground.html', context)


@csrf_exempt
@require_http_methods(['POST'])
def switch_demo_user(request):
    """Switch between demo users"""
    try:
        if not request.body:
            return JsonResponse({'error': 'No data provided'}, status=400)
            
        data = json.loads(request.body)
        username = data.get('username')
        
        if not username:
            return JsonResponse({'error': 'Username not provided'}, status=400)
        
        if username not in DEMO_USERS:
            available_users = ', '.join(DEMO_USERS.keys())
            return JsonResponse({
                'error': f'Invalid user: {username}',
                'available_users': available_users
            }, status=400)
        
        # Login to identity provider
        user_data = DEMO_USERS[username]
        login_response = requests.post(
            'http://identity-provider:8000/api/login/',
            json={
                'username': username,
                'password': user_data['password']
            }
        )
        
        if login_response.status_code == 200:
            login_data = login_response.json()
            request.session['demo_user'] = username
            request.session['demo_access_token'] = login_data.get('token')
            request.session['demo_user_data'] = user_data
            
            # Log successful switch
            logger.info(f"Demo user switched to {username}")
            
            return JsonResponse({
                'success': True,
                'user': username,
                'user_data': user_data,
                'access_token': login_data.get('token')
            })
        else:
            return JsonResponse({
                'error': 'Login failed',
                'details': login_response.text
            }, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(['POST'])
def test_api_endpoint(request):
    """Test an API endpoint with current user's token"""
    try:
        data = json.loads(request.body)
        service = data.get('service')
        endpoint = data.get('endpoint')
        method = data.get('method', 'GET')
        
        if service not in API_ENDPOINTS:
            return JsonResponse({'error': 'Invalid service'}, status=400)
        
        # Build request
        base_url = API_ENDPOINTS[service]['base_url']
        url = f"{base_url}{endpoint}"
        
        headers = {}
        access_token = request.session.get('demo_access_token')
        if access_token:
            headers['Authorization'] = f'Bearer {access_token}'
        
        # Make request
        response = requests.request(method, url, headers=headers)
        
        # Return response
        return JsonResponse({
            'success': response.status_code < 400,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'body': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'user': request.session.get('demo_user'),
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_user_permissions(request):
    """Get current user's permissions and attributes"""
    current_user = request.session.get('demo_user')
    if not current_user:
        return JsonResponse({'error': 'No user selected'}, status=400)
    
    user_data = DEMO_USERS.get(current_user, {})
    access_token = request.session.get('demo_access_token')
    
    # Get actual permissions from Redis
    actual_permissions = {}
    try:
        user_obj = User.objects.get(username=current_user)
        for service in ['billing_api', 'inventory_api', 'identity_provider']:
            try:
                attrs = get_user_attributes(user_obj.id, service)
                actual_permissions[service] = {
                    'roles': attrs.roles if attrs else [],
                    'attributes': attrs.__dict__ if attrs else {}
                }
            except:
                actual_permissions[service] = {'roles': [], 'attributes': {}}
    except User.DoesNotExist:
        pass
    
    # Also try to get from identity provider API
    api_permissions = {}
    if access_token:
        try:
            response = requests.get(
                'http://identity-provider:8000/api/profile/',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if response.status_code == 200:
                profile_data = response.json()
                api_permissions = profile_data.get('permissions', {})
        except:
            pass
    
    return JsonResponse({
        'user': current_user,
        'user_data': user_data,
        'expected_permissions': {
            'roles': user_data.get('expected_roles', {}),
            'attributes': user_data.get('expected_attrs', {})
        },
        'actual_permissions': actual_permissions,
        'api_permissions': api_permissions,
        'has_token': bool(access_token)
    })