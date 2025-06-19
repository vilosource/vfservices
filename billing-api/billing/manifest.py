"""
Billing service RBAC/ABAC manifest.
"""

BILLING_SERVICE_MANIFEST = {
    "service": "billing_api",
    "display_name": "Billing API Service",
    "description": "Handles invoicing, payments, and subscription management",
    "manifest_version": "1.0",
    "roles": [
        {
            "name": "billing_admin",
            "display_name": "Billing Administrator",
            "description": "Full access to all billing operations",
            "is_global": True
        },
        {
            "name": "invoice_viewer",
            "display_name": "Invoice Viewer",
            "description": "Can view invoices but not modify",
            "is_global": True
        },
        {
            "name": "invoice_manager",
            "display_name": "Invoice Manager",
            "description": "Can create, edit, and send invoices",
            "is_global": True
        },
        {
            "name": "invoice_sender",
            "display_name": "Invoice Sender",
            "description": "Can send invoices to customers",
            "is_global": True
        },
        {
            "name": "payment_viewer",
            "display_name": "Payment Viewer",
            "description": "Can view payment records",
            "is_global": True
        },
        {
            "name": "payment_processor",
            "display_name": "Payment Processor",
            "description": "Can process and update payment status",
            "is_global": True
        },
        {
            "name": "payment_manager",
            "display_name": "Payment Manager",
            "description": "Can manage payments including refunds",
            "is_global": True
        },
        {
            "name": "subscription_viewer",
            "display_name": "Subscription Viewer",
            "description": "Can view subscription details",
            "is_global": True
        },
        {
            "name": "subscription_manager",
            "display_name": "Subscription Manager",
            "description": "Can manage subscriptions including cancellations",
            "is_global": True
        },
        {
            "name": "subscription_renewal_agent",
            "display_name": "Subscription Renewal Agent",
            "description": "Can renew subscriptions",
            "is_global": True
        },
        {
            "name": "customer_manager",
            "display_name": "Customer Manager",
            "description": "Can manage customer records",
            "is_global": True
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
            "name": "customer_ids",
            "display_name": "Accessible Customer IDs",
            "description": "List of customer IDs user can access",
            "type": "list_integer",
            "is_required": False,
            "default_value": "[]"
        },
        {
            "name": "invoice_limit",
            "display_name": "Invoice Creation Limit",
            "description": "Maximum number of invoices user can create per month",
            "type": "integer",
            "is_required": False,
            "default_value": "100"
        },
        {
            "name": "payment_methods",
            "display_name": "Allowed Payment Methods",
            "description": "Payment methods the user can process",
            "type": "list_string",
            "is_required": False,
            "default_value": '["credit_card", "bank_transfer"]'
        },
        {
            "name": "max_refund_amount",
            "display_name": "Maximum Refund Amount",
            "description": "Maximum amount user can refund without approval",
            "type": "integer",
            "is_required": False,
            "default_value": "1000"
        }
    ]
}