"""
Azure Costs service RBAC/ABAC manifest.
"""

AZURE_COSTS_SERVICE_MANIFEST = {
    "service": "azure_costs",
    "display_name": "Azure Costs Service",
    "description": "Manages Azure subscription costs, budgets, and cost analysis",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "costs_viewer",
            "display_name": "Costs Viewer",
            "description": "Can view Azure costs and cost reports",
            "is_global": True
        },
        {
            "name": "costs_manager",
            "display_name": "Costs Manager",
            "description": "Can manage cost budgets and generate reports",
            "is_global": True
        },
        {
            "name": "costs_admin",
            "display_name": "Costs Administrator",
            "description": "Full access to all cost management operations",
            "is_global": True
        }
    ],
    "attributes": [
        {
            "name": "azure_subscription_ids",
            "display_name": "Azure Subscription IDs",
            "description": "List of Azure subscription IDs user can access",
            "type": "list_string",
            "is_required": False,
            "default_value": "[]"
        },
        {
            "name": "cost_center_ids",
            "display_name": "Cost Center IDs",
            "description": "List of cost center IDs user can manage",
            "type": "list_string",
            "is_required": False,
            "default_value": "[]"
        },
        {
            "name": "budget_limit",
            "display_name": "Budget Limit",
            "description": "Maximum budget amount user can set without approval",
            "type": "integer",
            "is_required": False,
            "default_value": "10000"
        },
        {
            "name": "can_export_reports",
            "display_name": "Can Export Reports",
            "description": "Whether user can export cost reports",
            "type": "boolean",
            "is_required": False,
            "default_value": "false"
        }
    ]
}