"""
Service manifest for the CIELO Website service.
Defines roles and attributes for CIELO cloud management access.
"""

SERVICE_MANIFEST = {
    "service": "cielo_website",
    "display_name": "CIELO Cloud Management",
    "description": "Cloud Infrastructure Excellence and Lifecycle Operations platform",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "cielo_admin",
            "display_name": "CIELO Administrator",
            "description": "Full administrative access to CIELO platform",
            "is_global": True
        },
        {
            "name": "cielo_user",
            "display_name": "CIELO User", 
            "description": "Standard access to CIELO cloud management features",
            "is_global": True
        },
        {
            "name": "cielo_viewer",
            "display_name": "CIELO Viewer",
            "description": "Read-only access to CIELO dashboards and reports",
            "is_global": True
        },
        {
            "name": "cloud_architect",
            "display_name": "Cloud Architect",
            "description": "Can design and modify cloud infrastructure",
            "is_global": True
        },
        {
            "name": "cost_analyst",
            "display_name": "Cost Analyst",
            "description": "Can view and analyze cloud costs and optimization opportunities",
            "is_global": True
        }
    ],
    "attributes": [
        {
            "name": "cloud_providers",
            "display_name": "Accessible Cloud Providers",
            "description": "List of cloud providers the user can manage (aws, azure, gcp)",
            "type": "list_string",
            "is_required": False,
            "default_value": '["azure"]'
        },
        {
            "name": "cost_center_ids",
            "display_name": "Cost Centers",
            "description": "List of cost center IDs the user can access",
            "type": "list_integer",
            "is_required": False,
            "default_value": "[]"
        },
        {
            "name": "max_resource_cost",
            "display_name": "Maximum Resource Cost",
            "description": "Maximum monthly cost for resources the user can provision",
            "type": "integer",
            "is_required": False,
            "default_value": "0"
        },
        {
            "name": "can_provision_resources",
            "display_name": "Can Provision Resources",
            "description": "Whether the user can create new cloud resources",
            "type": "boolean",
            "is_required": False,
            "default_value": "false"
        }
    ]
}