"""
Billing-specific ABAC policies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.rbac_abac.registry import register_policy


# Customer policies
@register_policy('customer_access')
def customer_access(user_attrs, obj=None, action=None):
    """
    Customer access policy:
    - billing_admin can access all customers
    - Users with customer_ids attribute can access those specific customers
    - Users can access customers in their department
    """
    if 'billing_admin' in user_attrs.roles:
        return True
    
    if obj and hasattr(user_attrs, 'customer_ids') and user_attrs.customer_ids:
        if obj.id in user_attrs.customer_ids:
            return True
    
    if obj and obj.department and user_attrs.department == obj.department:
        return True
    
    return False


@register_policy('customer_edit')
def customer_edit(user_attrs, obj=None, action=None):
    """Only billing_admin or customer_manager can edit customers."""
    return 'billing_admin' in user_attrs.roles or 'customer_manager' in user_attrs.roles


# Invoice policies
@register_policy('invoice_view')
def invoice_view(user_attrs, obj=None, action=None):
    """
    Invoice viewing policy:
    - billing_admin can view all invoices
    - invoice_viewer role can view all invoices
    - Users can view invoices in their department
    - Users can view invoices for customers they have access to
    """
    if 'billing_admin' in user_attrs.roles or 'invoice_viewer' in user_attrs.roles:
        return True
    
    if obj:
        # Department-based access
        if obj.department and user_attrs.department == obj.department:
            return True
        
        # Customer-based access
        if hasattr(user_attrs, 'customer_ids') and user_attrs.customer_ids:
            if obj.customer_id in user_attrs.customer_ids:
                return True
        
        # Creator can view their own invoices
        if obj.created_by_id == user_attrs.user_id:
            return True
    
    return False


@register_policy('invoice_edit')
def invoice_edit(user_attrs, obj=None, action=None):
    """
    Invoice editing policy:
    - billing_admin can edit all invoices
    - invoice_manager can edit invoices
    - Users can only edit draft invoices they created
    """
    if 'billing_admin' in user_attrs.roles or 'invoice_manager' in user_attrs.roles:
        return True
    
    if obj and obj.status == 'draft' and obj.created_by_id == user_attrs.user_id:
        return True
    
    return False


@register_policy('invoice_send')
def invoice_send(user_attrs, obj=None, action=None):
    """Only specific roles can send invoices."""
    allowed_roles = {'billing_admin', 'invoice_manager', 'invoice_sender'}
    return bool(allowed_roles.intersection(user_attrs.roles))


@register_policy('invoice_cancel')
def invoice_cancel(user_attrs, obj=None, action=None):
    """Only billing_admin can cancel invoices."""
    return 'billing_admin' in user_attrs.roles


# Payment policies
@register_policy('payment_view')
def payment_view(user_attrs, obj=None, action=None):
    """
    Payment viewing policy:
    - billing_admin can view all payments
    - payment_viewer role can view all payments
    - Users can view payments for invoices they can access
    """
    if 'billing_admin' in user_attrs.roles or 'payment_viewer' in user_attrs.roles:
        return True
    
    if obj and obj.invoice:
        # Delegate to invoice view policy
        return invoice_view(user_attrs, obj.invoice, 'view')
    
    return False


@register_policy('payment_processor')
def payment_processor(user_attrs, obj=None, action=None):
    """Only specific roles can process payments."""
    allowed_roles = {'billing_admin', 'payment_processor', 'payment_manager'}
    return bool(allowed_roles.intersection(user_attrs.roles))


@register_policy('payment_refund')
def payment_refund(user_attrs, obj=None, action=None):
    """Only billing_admin or payment_manager can issue refunds."""
    return 'billing_admin' in user_attrs.roles or 'payment_manager' in user_attrs.roles


# Subscription policies
@register_policy('subscription_view')
def subscription_view(user_attrs, obj=None, action=None):
    """
    Subscription viewing policy:
    - billing_admin can view all subscriptions
    - subscription_viewer role can view all subscriptions
    - Users can view subscriptions in their department
    - Users can view subscriptions for customers they have access to
    """
    if 'billing_admin' in user_attrs.roles or 'subscription_viewer' in user_attrs.roles:
        return True
    
    if obj:
        # Department-based access
        if obj.department and user_attrs.department == obj.department:
            return True
        
        # Customer-based access
        if hasattr(user_attrs, 'customer_ids') and user_attrs.customer_ids:
            if obj.customer_id in user_attrs.customer_ids:
                return True
    
    return False


@register_policy('subscription_edit')
def subscription_edit(user_attrs, obj=None, action=None):
    """
    Subscription editing policy:
    - billing_admin can edit all subscriptions
    - subscription_manager can edit subscriptions
    """
    return 'billing_admin' in user_attrs.roles or 'subscription_manager' in user_attrs.roles


@register_policy('subscription_cancel')
def subscription_cancel(user_attrs, obj=None, action=None):
    """
    Subscription cancellation policy:
    - billing_admin can cancel any subscription
    - subscription_manager can cancel subscriptions
    - Users can cancel trial subscriptions they created
    """
    if 'billing_admin' in user_attrs.roles or 'subscription_manager' in user_attrs.roles:
        return True
    
    if obj and obj.status == 'trial' and obj.created_by_id == user_attrs.user_id:
        return True
    
    return False


@register_policy('subscription_renew')
def subscription_renew(user_attrs, obj=None, action=None):
    """Only specific roles can renew subscriptions."""
    allowed_roles = {'billing_admin', 'subscription_manager', 'subscription_renewal_agent'}
    return bool(allowed_roles.intersection(user_attrs.roles))


# General billing policies
@register_policy('billing_admin_only')
def billing_admin_only(user_attrs, obj=None, action=None):
    """Only billing_admin role has access."""
    return 'billing_admin' in user_attrs.roles