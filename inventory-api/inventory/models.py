"""
Inventory models with RBAC-ABAC support.
"""

from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Import RBAC-ABAC components
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from common.rbac_abac.mixins import ABACModelMixin
from common.rbac_abac.querysets import ABACManager


class Category(ABACModelMixin, models.Model):
    """Product category with ABAC support."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'public_access',  # Categories are public
        'edit': 'inventory_manager',
        'delete': 'inventory_admin_only'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]


class Warehouse(ABACModelMixin, models.Model):
    """Warehouse/location model with ABAC support."""
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=20)
    department = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'warehouse_view',
        'edit': 'warehouse_edit',
        'delete': 'inventory_admin_only'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['department']),
            models.Index(fields=['manager']),
        ]


class Product(ABACModelMixin, models.Model):
    """Product model with ABAC support."""
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    weight = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'), help_text="Weight in kg")
    dimensions = models.JSONField(default=dict, blank=True, help_text="Dimensions in cm (length, width, height)")
    is_active = models.BooleanField(default=True)
    department = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'product_view',
        'edit': 'product_edit',
        'delete': 'inventory_admin_only',
        'adjust_price': 'pricing_manager'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
    
    class Meta:
        ordering = ['sku']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category']),
            models.Index(fields=['department']),
            models.Index(fields=['created_by']),
        ]


class StockLevel(ABACModelMixin, models.Model):
    """Stock level tracking with ABAC support."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_levels')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_levels')
    quantity_on_hand = models.IntegerField(default=0)
    quantity_reserved = models.IntegerField(default=0)
    quantity_available = models.IntegerField(default=0)
    reorder_point = models.IntegerField(default=0)
    reorder_quantity = models.IntegerField(default=0)
    last_counted_date = models.DateTimeField(null=True, blank=True)
    last_counted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='counted_stock')
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'stock_view',
        'edit': 'stock_edit',
        'delete': 'inventory_admin_only',
        'count': 'stock_counter',
        'adjust': 'stock_adjuster'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    @property
    def department(self):
        """Get department from warehouse."""
        return self.warehouse.department if self.warehouse else None
    
    def save(self, *args, **kwargs):
        # Calculate available quantity
        self.quantity_available = self.quantity_on_hand - self.quantity_reserved
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.sku} @ {self.warehouse.code}: {self.quantity_available} available"
    
    class Meta:
        unique_together = [('product', 'warehouse')]
        ordering = ['product', 'warehouse']
        indexes = [
            models.Index(fields=['product', 'warehouse']),
            models.Index(fields=['warehouse']),
        ]


class StockMovement(ABACModelMixin, models.Model):
    """Stock movement history with ABAC support."""
    
    MOVEMENT_TYPES = [
        ('receipt', 'Receipt'),
        ('shipment', 'Shipment'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
        ('count', 'Physical Count'),
        ('return', 'Return'),
    ]
    
    movement_id = models.CharField(max_length=50, unique=True)
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='movements')
    from_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='outbound_movements')
    to_warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True, related_name='inbound_movements')
    quantity = models.IntegerField()
    reference_number = models.CharField(max_length=100, blank=True, help_text="PO number, invoice number, etc.")
    notes = models.TextField(blank=True)
    movement_date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_movements')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'movement_view',
        'edit': 'movement_edit',
        'delete': 'inventory_admin_only',
        'approve': 'movement_approver'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    @property
    def department(self):
        """Get department from warehouses."""
        if self.from_warehouse:
            return self.from_warehouse.department
        elif self.to_warehouse:
            return self.to_warehouse.department
        return None
    
    def __str__(self):
        return f"{self.movement_id} - {self.movement_type} ({self.quantity} {self.product.sku})"
    
    class Meta:
        ordering = ['-movement_date']
        indexes = [
            models.Index(fields=['movement_id']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['product']),
            models.Index(fields=['created_by']),
            models.Index(fields=['movement_date']),
        ]


class InventoryCount(ABACModelMixin, models.Model):
    """Physical inventory count with ABAC support."""
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    count_id = models.CharField(max_length=50, unique=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_counts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    count_date = models.DateField()
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_counts')
    assigned_to = models.ManyToManyField(User, related_name='assigned_counts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'count_view',
        'edit': 'count_edit',
        'delete': 'inventory_admin_only',
        'start': 'count_starter',
        'complete': 'count_completer'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    @property
    def department(self):
        """Get department from warehouse."""
        return self.warehouse.department if self.warehouse else None
    
    def __str__(self):
        return f"Count {self.count_id} - {self.warehouse.code} ({self.status})"
    
    class Meta:
        ordering = ['-count_date']
        indexes = [
            models.Index(fields=['count_id']),
            models.Index(fields=['warehouse', 'status']),
            models.Index(fields=['created_by']),
        ]