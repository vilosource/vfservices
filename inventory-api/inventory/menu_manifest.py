"""
Menu manifest for inventory service.
Defines menu contributions that this service provides.
"""

MENU_CONTRIBUTIONS = {
    'sidebar_menu': {
        'items': [
            {
                'id': 'inventory_main',
                'label': 'Inventory',
                'url': '/inventory/',
                'icon': 'box',
                'order': 100,
                'permissions': ['inventory.view_product'],
                'app_name': 'inventory',
                'children': [
                    {
                        'id': 'inventory_products',
                        'label': 'Products',
                        'url': '/inventory/products/',
                        'permissions': ['inventory.view_product'],
                        'children': [
                            {
                                'id': 'products_all',
                                'label': 'All Products',
                                'url': '/inventory/products/all/',
                                'permissions': ['inventory.view_product']
                            },
                            {
                                'id': 'products_active',
                                'label': 'Active Products',
                                'url': '/inventory/products/active/',
                                'permissions': ['inventory.view_product']
                            },
                            {
                                'id': 'products_discontinued',
                                'label': 'Discontinued',
                                'url': '/inventory/products/discontinued/',
                                'permissions': ['inventory.view_product']
                            }
                        ]
                    },
                    {
                        'id': 'inventory_categories',
                        'label': 'Categories',
                        'url': '/inventory/categories/',
                        'permissions': ['inventory.view_category'],
                        'children': [
                            {
                                'id': 'categories_hierarchy',
                                'label': 'Category Tree',
                                'url': '/inventory/categories/tree/',
                                'permissions': ['inventory.view_category']
                            },
                            {
                                'id': 'categories_manage',
                                'label': 'Manage Categories',
                                'url': '/inventory/categories/manage/',
                                'permissions': ['inventory.add_category']
                            }
                        ]
                    },
                    {
                        'id': 'inventory_warehouse',
                        'label': 'Warehouse',
                        'url': '/inventory/warehouse/',
                        'permissions': ['inventory.view_product'],
                        'children': [
                            {
                                'id': 'warehouse_stock',
                                'label': 'Stock Levels',
                                'url': '/inventory/warehouse/stock/',
                                'permissions': ['inventory.view_product'],
                                'children': [
                                    {
                                        'id': 'stock_by_location',
                                        'label': 'By Location',
                                        'url': '/inventory/warehouse/stock/location/',
                                        'permissions': ['inventory.view_product']
                                    },
                                    {
                                        'id': 'stock_alerts',
                                        'label': 'Low Stock Alerts',
                                        'url': '/inventory/warehouse/stock/alerts/',
                                        'permissions': ['inventory.view_product']
                                    }
                                ]
                            },
                            {
                                'id': 'warehouse_transfers',
                                'label': 'Transfers',
                                'url': '/inventory/warehouse/transfers/',
                                'permissions': ['inventory.view_transfer'],
                                'children': [
                                    {
                                        'id': 'transfers_pending',
                                        'label': 'Pending',
                                        'url': '/inventory/warehouse/transfers/pending/',
                                        'permissions': ['inventory.view_transfer']
                                    },
                                    {
                                        'id': 'transfers_completed',
                                        'label': 'Completed',
                                        'url': '/inventory/warehouse/transfers/completed/',
                                        'permissions': ['inventory.view_transfer']
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'id': 'inventory_suppliers',
                        'label': 'Suppliers',
                        'url': '/inventory/suppliers/',
                        'permissions': ['inventory.view_supplier']
                    },
                    {
                        'id': 'inventory_reports',
                        'label': 'Reports',
                        'url': '/inventory/reports/',
                        'permissions': ['inventory.view_product'],
                        'children': [
                            {
                                'id': 'reports_inventory',
                                'label': 'Inventory Reports',
                                'url': '/inventory/reports/inventory/',
                                'permissions': ['inventory.view_product']
                            },
                            {
                                'id': 'reports_movement',
                                'label': 'Stock Movement',
                                'url': '/inventory/reports/movement/',
                                'permissions': ['inventory.view_product']
                            },
                            {
                                'id': 'reports_analytics',
                                'label': 'Analytics',
                                'url': '/inventory/reports/analytics/',
                                'permissions': ['inventory.view_product'],
                                'children': [
                                    {
                                        'id': 'analytics_trends',
                                        'label': 'Trends',
                                        'url': '/inventory/reports/analytics/trends/',
                                        'permissions': ['inventory.view_product']
                                    },
                                    {
                                        'id': 'analytics_forecast',
                                        'label': 'Forecast',
                                        'url': '/inventory/reports/analytics/forecast/',
                                        'permissions': ['inventory.view_product']
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    },
    'top_menu': {
        'items': [
            {
                'id': 'inventory_quick_add',
                'label': 'Add Product',
                'url': '/inventory/products/add/',
                'icon': 'plus-circle',
                'order': 50,
                'permissions': ['inventory.add_product'],
                'app_name': 'inventory'
            }
        ]
    }
}