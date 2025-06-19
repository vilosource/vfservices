"""
Inventory-specific ABAC policies.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.rbac_abac.registry import register_policy


# Warehouse policies
@register_policy('warehouse_view')
def warehouse_view(user_attrs, obj=None, action=None):
    """
    Warehouse viewing policy:
    - inventory_admin can view all warehouses
    - warehouse_viewer role can view all warehouses
    - Warehouse managers can view their warehouses
    - Users can view warehouses in their department
    """
    if 'inventory_admin' in user_attrs.roles or 'warehouse_viewer' in user_attrs.roles:
        return True
    
    if obj:
        # Manager can view their warehouse
        if obj.manager_id == user_attrs.user_id:
            return True
        
        # Department-based access
        if obj.department and user_attrs.department == obj.department:
            return True
    
    return False


@register_policy('warehouse_edit')
def warehouse_edit(user_attrs, obj=None, action=None):
    """
    Warehouse editing policy:
    - inventory_admin can edit all warehouses
    - warehouse_manager role can edit warehouses
    - Specific warehouse managers can edit their assigned warehouse
    """
    if 'inventory_admin' in user_attrs.roles or 'warehouse_manager' in user_attrs.roles:
        return True
    
    if obj and obj.manager_id == user_attrs.user_id:
        return True
    
    return False


# Product policies
@register_policy('product_view')
def product_view(user_attrs, obj=None, action=None):
    """
    Product viewing policy:
    - inventory_admin can view all products
    - product_viewer role can view all products
    - Users can view products in their department
    - Public products (no department) are viewable by all authenticated users
    """
    if 'inventory_admin' in user_attrs.roles or 'product_viewer' in user_attrs.roles:
        return True
    
    if obj:
        # Public products (no department set)
        if not obj.department:
            return True
        
        # Department-based access
        if obj.department == user_attrs.department:
            return True
    
    # Authenticated users can at least browse products
    return user_attrs.is_authenticated


@register_policy('product_edit')
def product_edit(user_attrs, obj=None, action=None):
    """
    Product editing policy:
    - inventory_admin can edit all products
    - product_manager can edit products
    - Users who created a product can edit it
    """
    if 'inventory_admin' in user_attrs.roles or 'product_manager' in user_attrs.roles:
        return True
    
    if obj and obj.created_by_id == user_attrs.user_id:
        return True
    
    return False


@register_policy('pricing_manager')
def pricing_manager(user_attrs, obj=None, action=None):
    """Only specific roles can adjust product pricing."""
    allowed_roles = {'inventory_admin', 'pricing_manager', 'product_manager'}
    return bool(allowed_roles.intersection(user_attrs.roles))


# Stock policies
@register_policy('stock_view')
def stock_view(user_attrs, obj=None, action=None):
    """
    Stock level viewing policy:
    - inventory_admin can view all stock levels
    - stock_viewer role can view all stock levels
    - Warehouse managers can view stock in their warehouse
    - Users can view stock in warehouses of their department
    """
    if 'inventory_admin' in user_attrs.roles or 'stock_viewer' in user_attrs.roles:
        return True
    
    if obj and obj.warehouse:
        # Warehouse manager access
        if obj.warehouse.manager_id == user_attrs.user_id:
            return True
        
        # Department-based access
        if obj.warehouse.department and user_attrs.department == obj.warehouse.department:
            return True
    
    return False


@register_policy('stock_edit')
def stock_edit(user_attrs, obj=None, action=None):
    """
    Stock editing policy:
    - inventory_admin can edit all stock levels
    - stock_manager can edit stock levels
    - Warehouse managers can edit stock in their warehouse
    """
    if 'inventory_admin' in user_attrs.roles or 'stock_manager' in user_attrs.roles:
        return True
    
    if obj and obj.warehouse and obj.warehouse.manager_id == user_attrs.user_id:
        return True
    
    return False


@register_policy('stock_counter')
def stock_counter(user_attrs, obj=None, action=None):
    """Users who can perform stock counts."""
    allowed_roles = {'inventory_admin', 'stock_manager', 'stock_counter', 'warehouse_staff'}
    return bool(allowed_roles.intersection(user_attrs.roles))


@register_policy('stock_adjuster')
def stock_adjuster(user_attrs, obj=None, action=None):
    """Users who can make stock adjustments."""
    allowed_roles = {'inventory_admin', 'stock_manager', 'stock_adjuster'}
    return bool(allowed_roles.intersection(user_attrs.roles))


# Movement policies
@register_policy('movement_view')
def movement_view(user_attrs, obj=None, action=None):
    """
    Stock movement viewing policy:
    - inventory_admin can view all movements
    - movement_viewer role can view all movements
    - Users can view movements for their warehouses/department
    - Users can view movements they created
    """
    if 'inventory_admin' in user_attrs.roles or 'movement_viewer' in user_attrs.roles:
        return True
    
    if obj:
        # Creator can view their movements
        if obj.created_by_id == user_attrs.user_id:
            return True
        
        # Department-based access through warehouses
        if obj.from_warehouse and obj.from_warehouse.department == user_attrs.department:
            return True
        if obj.to_warehouse and obj.to_warehouse.department == user_attrs.department:
            return True
        
        # Warehouse manager access
        if obj.from_warehouse and obj.from_warehouse.manager_id == user_attrs.user_id:
            return True
        if obj.to_warehouse and obj.to_warehouse.manager_id == user_attrs.user_id:
            return True
    
    return False


@register_policy('movement_edit')
def movement_edit(user_attrs, obj=None, action=None):
    """
    Movement editing policy:
    - inventory_admin can edit all movements
    - movement_manager can edit movements
    - Users can edit draft movements they created
    """
    if 'inventory_admin' in user_attrs.roles or 'movement_manager' in user_attrs.roles:
        return True
    
    if obj and obj.created_by_id == user_attrs.user_id:
        # Allow editing own movements within reasonable time (e.g., same day)
        from django.utils import timezone
        if (timezone.now() - obj.created_at).days < 1:
            return True
    
    return False


@register_policy('movement_approver')
def movement_approver(user_attrs, obj=None, action=None):
    """Users who can approve stock movements."""
    allowed_roles = {'inventory_admin', 'movement_approver', 'warehouse_manager'}
    return bool(allowed_roles.intersection(user_attrs.roles))


# Inventory count policies
@register_policy('count_view')
def count_view(user_attrs, obj=None, action=None):
    """
    Inventory count viewing policy:
    - inventory_admin can view all counts
    - count_viewer role can view all counts
    - Assigned users can view their counts
    - Warehouse managers can view counts for their warehouse
    """
    if 'inventory_admin' in user_attrs.roles or 'count_viewer' in user_attrs.roles:
        return True
    
    if obj:
        # Creator can view
        if obj.created_by_id == user_attrs.user_id:
            return True
        
        # Assigned users can view
        if hasattr(obj, 'assigned_to') and user_attrs.user_id in obj.assigned_to.values_list('id', flat=True):
            return True
        
        # Warehouse manager can view
        if obj.warehouse and obj.warehouse.manager_id == user_attrs.user_id:
            return True
        
        # Department access
        if obj.warehouse and obj.warehouse.department == user_attrs.department:
            return True
    
    return False


@register_policy('count_edit')
def count_edit(user_attrs, obj=None, action=None):
    """
    Count editing policy:
    - inventory_admin can edit all counts
    - count_manager can edit counts
    - Warehouse managers can edit counts for their warehouse
    """
    if 'inventory_admin' in user_attrs.roles or 'count_manager' in user_attrs.roles:
        return True
    
    if obj and obj.warehouse and obj.warehouse.manager_id == user_attrs.user_id:
        return True
    
    return False


@register_policy('count_starter')
def count_starter(user_attrs, obj=None, action=None):
    """Users who can start inventory counts."""
    allowed_roles = {'inventory_admin', 'count_manager', 'warehouse_manager', 'count_supervisor'}
    return bool(allowed_roles.intersection(user_attrs.roles))


@register_policy('count_completer')
def count_completer(user_attrs, obj=None, action=None):
    """Users who can complete/finalize inventory counts."""
    allowed_roles = {'inventory_admin', 'count_manager', 'warehouse_manager'}
    return bool(allowed_roles.intersection(user_attrs.roles))


# General inventory policies
@register_policy('inventory_admin_only')
def inventory_admin_only(user_attrs, obj=None, action=None):
    """Only inventory_admin role has access."""
    return 'inventory_admin' in user_attrs.roles


@register_policy('inventory_manager')
def inventory_manager(user_attrs, obj=None, action=None):
    """Inventory admin or manager roles."""
    return 'inventory_admin' in user_attrs.roles or 'inventory_manager' in user_attrs.roles