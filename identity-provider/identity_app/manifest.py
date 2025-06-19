"""
Service manifest for the Identity Provider service.
Defines roles and attributes for identity and user management.
"""

SERVICE_MANIFEST = {
    "service": {
        "name": "identity_provider",
        "display_name": "Identity Provider",
        "description": "Central authentication and user management service"
    },
    "roles": [
        {
            "name": "customer_manager",
            "display_name": "Customer Manager",
            "description": "Can manage customer records and relationships",
            "is_global": True
        },
        {
            "name": "user_admin",
            "display_name": "User Administrator", 
            "description": "Can create, modify, and delete user accounts",
            "is_global": True
        },
        {
            "name": "role_manager",
            "display_name": "Role Manager",
            "description": "Can assign and revoke roles for users",
            "is_global": True
        },
        {
            "name": "identity_viewer",
            "display_name": "Identity Viewer",
            "description": "Can view user information and roles",
            "is_global": True
        }
    ],
    "attributes": [
        {
            "name": "can_manage_customers",
            "display_name": "Can Manage Customers",
            "description": "Whether the user can create and modify customer records",
            "attribute_type": "boolean",
            "is_required": False,
            "default_value": False
        },
        {
            "name": "managed_customer_types",
            "display_name": "Managed Customer Types",
            "description": "Types of customers the user can manage",
            "attribute_type": "list_string",
            "is_required": False,
            "default_value": []
        }
    ]
}