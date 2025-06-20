"""
Constants and configuration for Identity Admin app
"""

# Role profiles for quick assignment
ROLE_PROFILES = {
    'super_admin': {
        'name': 'Super Administrator',
        'description': 'Full system access',
        'roles': [
            ('identity_admin', 'identity_provider'),
            ('billing_admin', 'billing_api'),
            ('inventory_admin', 'inventory_api'),
            ('costs_admin', 'azure_costs'),
            ('cielo_admin', 'cielo_website'),
        ]
    },
    'operations_manager': {
        'name': 'Operations Manager',
        'description': 'Manages inventory and warehouse operations',
        'roles': [
            ('inventory_manager', 'inventory_api'),
            ('warehouse_manager', 'inventory_api'),
            ('movement_manager', 'inventory_api'),
        ]
    },
    'finance_manager': {
        'name': 'Finance Manager',
        'description': 'Manages billing and costs',
        'roles': [
            ('billing_admin', 'billing_api'),
            ('costs_manager', 'azure_costs'),
            ('payment_manager', 'billing_api'),
        ]
    },
    'customer_service': {
        'name': 'Customer Service Representative',
        'description': 'Handles customer accounts and subscriptions',
        'roles': [
            ('customer_manager', 'identity_provider'),
            ('invoice_manager', 'billing_api'),
            ('subscription_manager', 'billing_api'),
        ]
    },
    'cost_analyst': {
        'name': 'Cost Analyst',
        'description': 'Analyzes costs and cloud usage',
        'roles': [
            ('costs_viewer', 'azure_costs'),
            ('cost_analyst', 'cielo_website'),
            ('cielo_viewer', 'cielo_website'),
        ]
    },
    'warehouse_supervisor': {
        'name': 'Warehouse Supervisor',
        'description': 'Supervises warehouse operations',
        'roles': [
            ('warehouse_manager', 'inventory_api'),
            ('stock_manager', 'inventory_api'),
            ('count_supervisor', 'inventory_api'),
        ]
    },
    'auditor': {
        'name': 'Auditor',
        'description': 'Read-only access for audit purposes',
        'roles': [
            ('identity_viewer', 'identity_provider'),
            ('invoice_viewer', 'billing_api'),
            ('payment_viewer', 'billing_api'),
            ('costs_viewer', 'azure_costs'),
            ('movement_viewer', 'inventory_api'),
        ]
    }
}

# Default settings
DEFAULT_PAGE_SIZE = 50
DEFAULT_API_TIMEOUT = 30  # seconds