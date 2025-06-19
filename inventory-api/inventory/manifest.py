"""
Inventory service RBAC/ABAC manifest.
"""

INVENTORY_SERVICE_MANIFEST = {
    "service": "inventory_api",
    "display_name": "Inventory API Service",
    "description": "Manages products, warehouses, stock levels, and inventory movements",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "inventory_admin",
            "display_name": "Inventory Administrator",
            "description": "Full access to all inventory operations",
            "is_global": True
        },
        {
            "name": "inventory_manager",
            "display_name": "Inventory Manager",
            "description": "Can manage most inventory operations",
            "is_global": True
        },
        {
            "name": "warehouse_manager",
            "display_name": "Warehouse Manager",
            "description": "Can manage specific warehouse operations",
            "is_global": False
        },
        {
            "name": "warehouse_viewer",
            "display_name": "Warehouse Viewer",
            "description": "Can view warehouse information",
            "is_global": True
        },
        {
            "name": "warehouse_staff",
            "display_name": "Warehouse Staff",
            "description": "Can perform basic warehouse operations",
            "is_global": False
        },
        {
            "name": "product_viewer",
            "display_name": "Product Viewer",
            "description": "Can view product information",
            "is_global": True
        },
        {
            "name": "product_manager",
            "display_name": "Product Manager",
            "description": "Can create and edit products",
            "is_global": True
        },
        {
            "name": "pricing_manager",
            "display_name": "Pricing Manager",
            "description": "Can adjust product pricing",
            "is_global": True
        },
        {
            "name": "stock_viewer",
            "display_name": "Stock Viewer",
            "description": "Can view stock levels",
            "is_global": True
        },
        {
            "name": "stock_manager",
            "display_name": "Stock Manager",
            "description": "Can manage stock levels and adjustments",
            "is_global": True
        },
        {
            "name": "stock_counter",
            "display_name": "Stock Counter",
            "description": "Can perform stock counts",
            "is_global": False
        },
        {
            "name": "stock_adjuster",
            "display_name": "Stock Adjuster",
            "description": "Can make stock adjustments",
            "is_global": True
        },
        {
            "name": "movement_viewer",
            "display_name": "Movement Viewer",
            "description": "Can view stock movements",
            "is_global": True
        },
        {
            "name": "movement_manager",
            "display_name": "Movement Manager",
            "description": "Can manage stock movements",
            "is_global": True
        },
        {
            "name": "movement_approver",
            "display_name": "Movement Approver",
            "description": "Can approve stock movements",
            "is_global": True
        },
        {
            "name": "count_viewer",
            "display_name": "Count Viewer",
            "description": "Can view inventory counts",
            "is_global": True
        },
        {
            "name": "count_manager",
            "display_name": "Count Manager",
            "description": "Can manage inventory counts",
            "is_global": True
        },
        {
            "name": "count_supervisor",
            "display_name": "Count Supervisor",
            "description": "Can supervise inventory counts",
            "is_global": False
        }
    ],
    "attributes": [
        {
            "name": "department",
            "display_name": "Department",
            "description": "User's department for access control",
            "type": "string",
            "is_required": False
        },
        {
            "name": "warehouse_ids",
            "display_name": "Accessible Warehouse IDs",
            "description": "List of warehouse IDs user can access",
            "type": "list_integer",
            "is_required": False,
            "default_value": "[]"
        },
        {
            "name": "product_categories",
            "display_name": "Product Categories",
            "description": "Product categories the user can manage",
            "type": "list_string",
            "is_required": False,
            "default_value": "[]"
        },
        {
            "name": "max_adjustment_value",
            "display_name": "Maximum Adjustment Value",
            "description": "Maximum value of stock adjustments user can make",
            "type": "integer",
            "is_required": False,
            "default_value": "10000"
        },
        {
            "name": "movement_types",
            "display_name": "Allowed Movement Types",
            "description": "Types of stock movements user can create",
            "type": "list_string",
            "is_required": False,
            "default_value": '["adjustment", "transfer"]'
        },
        {
            "name": "can_export_data",
            "display_name": "Can Export Data",
            "description": "Whether user can export inventory data",
            "type": "boolean",
            "is_required": False,
            "default_value": "false"
        }
    ]
}