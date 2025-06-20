"""
Azure Costs service ABAC policies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.rbac_abac.registry import register_policy


# Cost viewing policies
@register_policy('costs_view')
def costs_view(user_attrs, obj=None, action=None):
    """
    Cost viewing policy:
    - costs_admin can view all costs
    - costs_manager can view all costs
    - costs_viewer can view costs
    - Users can view costs for their assigned subscriptions
    - Users can view costs for their assigned cost centers
    """
    # Role-based access
    if any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager', 'costs_viewer']):
        return True
    
    # Subscription-based access
    if obj and hasattr(obj, 'subscription_id'):
        if obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
    
    # Cost center-based access
    if obj and hasattr(obj, 'cost_center_id'):
        if obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


@register_policy('costs_analyze')
def costs_analyze(user_attrs, obj=None, action=None):
    """
    Cost analysis policy:
    - costs_admin can perform all analysis
    - costs_manager can perform all analysis
    - costs_viewer with specific subscription/cost center access
    """
    # Role-based access
    if any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager']):
        return True
    
    # Viewers need specific permissions
    if 'costs_viewer' in user_attrs.roles:
        # Check if they have access to the requested subscription/cost center
        if obj:
            if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
                return True
            if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
                return True
    
    return False


# Budget management policies
@register_policy('budget_view')
def budget_view(user_attrs, obj=None, action=None):
    """
    Budget viewing policy:
    - costs_admin can view all budgets
    - costs_manager can view all budgets
    - costs_viewer can view budgets
    - Users can view budgets for their subscriptions/cost centers
    """
    # Role-based access
    if any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager', 'costs_viewer']):
        return True
    
    # Attribute-based access
    if obj:
        if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


@register_policy('budget_create')
def budget_create(user_attrs, obj=None, action=None):
    """
    Budget creation policy:
    - costs_admin can create any budget
    - costs_manager can create budgets within their limit
    - Users need budget creation permission and must respect their budget_limit
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if 'costs_manager' in user_attrs.roles:
        # Check if within budget limit
        if obj and hasattr(obj, 'amount'):
            if obj.amount <= user_attrs.budget_limit:
                return True
            else:
                # Would need approval for higher amounts
                return False
        return True
    
    return False


@register_policy('budget_edit')
def budget_edit(user_attrs, obj=None, action=None):
    """
    Budget editing policy:
    - costs_admin can edit any budget
    - costs_manager can edit budgets they manage
    - Users can edit budgets they created within their limit
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if 'costs_manager' in user_attrs.roles:
        if obj:
            # Can edit if they manage the subscription/cost center
            if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
                # Check if new amount is within limit
                if hasattr(obj, 'amount') and obj.amount <= user_attrs.budget_limit:
                    return True
            if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
                if hasattr(obj, 'amount') and obj.amount <= user_attrs.budget_limit:
                    return True
    
    # Creator can edit their own budgets
    if obj and hasattr(obj, 'created_by_id') and obj.created_by_id == user_attrs.user_id:
        if hasattr(obj, 'amount') and obj.amount <= user_attrs.budget_limit:
            return True
    
    return False


@register_policy('budget_delete')
def budget_delete(user_attrs, obj=None, action=None):
    """
    Budget deletion policy:
    - costs_admin can delete any budget
    - costs_manager can delete budgets they manage
    - Users can delete budgets they created
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if 'costs_manager' in user_attrs.roles and obj:
        # Can delete if they manage the subscription/cost center
        if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    # Creator can delete their own budgets
    if obj and hasattr(obj, 'created_by_id') and obj.created_by_id == user_attrs.user_id:
        return True
    
    return False


# Report export policies
@register_policy('report_export')
def report_export(user_attrs, obj=None, action=None):
    """
    Report export policy:
    - costs_admin can export any report
    - costs_manager can export reports
    - Users with can_export_reports=true can export reports for their subscriptions/cost centers
    """
    if any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager']):
        return True
    
    # Check explicit export permission
    if user_attrs.can_export_reports:
        # If no specific object, allow export of permitted resources
        if not obj:
            return True
        
        # Check if they have access to the specific resource
        if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


@register_policy('report_schedule')
def report_schedule(user_attrs, obj=None, action=None):
    """
    Report scheduling policy:
    - costs_admin can schedule any reports
    - costs_manager can schedule reports for their resources
    - Regular users cannot schedule reports
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if 'costs_manager' in user_attrs.roles:
        # Can schedule reports for managed resources
        if not obj:
            return True
        
        if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


# Subscription access policies
@register_policy('subscription_view')
def subscription_view(user_attrs, obj=None, action=None):
    """
    Subscription viewing policy:
    - costs_admin can view all subscriptions
    - Users can view subscriptions in their azure_subscription_ids list
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if obj and hasattr(obj, 'subscription_id'):
        if obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
    
    # Allow listing of accessible subscriptions
    if not obj and user_attrs.azure_subscription_ids:
        return True
    
    return False


@register_policy('subscription_manage')
def subscription_manage(user_attrs, obj=None, action=None):
    """
    Subscription management policy:
    - Only costs_admin can manage subscription configurations
    """
    return 'costs_admin' in user_attrs.roles


# Cost center policies
@register_policy('cost_center_view')
def cost_center_view(user_attrs, obj=None, action=None):
    """
    Cost center viewing policy:
    - costs_admin can view all cost centers
    - costs_manager can view all cost centers
    - Users can view cost centers in their cost_center_ids list
    """
    if any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager']):
        return True
    
    if obj and hasattr(obj, 'cost_center_id'):
        if obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    # Allow listing of accessible cost centers
    if not obj and user_attrs.cost_center_ids:
        return True
    
    return False


@register_policy('cost_center_manage')
def cost_center_manage(user_attrs, obj=None, action=None):
    """
    Cost center management policy:
    - costs_admin can manage all cost centers
    - costs_manager can manage assigned cost centers
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if 'costs_manager' in user_attrs.roles and obj:
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


# Alert policies
@register_policy('alert_view')
def alert_view(user_attrs, obj=None, action=None):
    """
    Alert viewing policy:
    - costs_admin can view all alerts
    - costs_manager can view all alerts
    - Users can view alerts for their subscriptions/cost centers
    """
    if any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager']):
        return True
    
    if obj:
        if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


@register_policy('alert_manage')
def alert_manage(user_attrs, obj=None, action=None):
    """
    Alert management policy:
    - costs_admin can manage all alerts
    - costs_manager can manage alerts for their resources
    """
    if 'costs_admin' in user_attrs.roles:
        return True
    
    if 'costs_manager' in user_attrs.roles:
        if not obj:
            return True
        
        if hasattr(obj, 'subscription_id') and obj.subscription_id in user_attrs.azure_subscription_ids:
            return True
        if hasattr(obj, 'cost_center_id') and obj.cost_center_id in user_attrs.cost_center_ids:
            return True
    
    return False


# Approval policies
@register_policy('budget_approval_required')
def budget_approval_required(user_attrs, obj=None, action=None):
    """
    Determines if budget approval is required:
    - costs_admin never needs approval
    - Others need approval if budget exceeds their limit
    """
    if 'costs_admin' in user_attrs.roles:
        return False  # No approval needed
    
    if obj and hasattr(obj, 'amount'):
        return obj.amount > user_attrs.budget_limit
    
    return True  # Default to requiring approval


@register_policy('budget_approve')
def budget_approve(user_attrs, obj=None, action=None):
    """
    Budget approval policy:
    - Only costs_admin can approve budgets
    """
    return 'costs_admin' in user_attrs.roles


# Administrative policies
@register_policy('costs_admin_only')
def costs_admin_only(user_attrs, obj=None, action=None):
    """Only costs_admin role has access."""
    return 'costs_admin' in user_attrs.roles


@register_policy('costs_management')
def costs_management(user_attrs, obj=None, action=None):
    """Costs admin or manager roles."""
    return any(role in user_attrs.roles for role in ['costs_admin', 'costs_manager'])