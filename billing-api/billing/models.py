"""
Billing models with RBAC-ABAC support.
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


class Customer(ABACModelMixin, models.Model):
    """Customer model with ABAC support."""
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    company = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_customers')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'customer_access',
        'edit': 'customer_edit',
        'delete': 'billing_admin_only'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['department']),
        ]


class Invoice(ABACModelMixin, models.Model):
    """Invoice model with ABAC support."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    department = models.CharField(max_length=100, blank=True)
    issue_date = models.DateField(default=timezone.now)
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_invoices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'invoice_view',
        'edit': 'invoice_edit',
        'delete': 'billing_admin_only',
        'send': 'invoice_send',
        'cancel': 'invoice_cancel'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name}"
    
    def save(self, *args, **kwargs):
        # Copy department from customer if not set
        if not self.department and self.customer:
            self.department = self.customer.department
        
        # Calculate total
        self.tax_amount = self.subtotal * (self.tax_rate / 100)
        self.total = self.subtotal + self.tax_amount
        
        super().save(*args, **kwargs)
    
    class Meta:
        ordering = ['-issue_date', '-invoice_number']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['department']),
            models.Index(fields=['created_by']),
        ]


class InvoiceItem(models.Model):
    """Individual line items on an invoice."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    description = models.CharField(max_length=500)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.description} ({self.quantity} x {self.unit_price})"
    
    class Meta:
        ordering = ['id']


class Payment(ABACModelMixin, models.Model):
    """Payment model with ABAC support."""
    
    METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    payment_id = models.CharField(max_length=50, unique=True)
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='processed_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'payment_view',
        'edit': 'payment_processor',
        'delete': 'billing_admin_only',
        'process': 'payment_processor',
        'refund': 'payment_refund'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    @property
    def department(self):
        """Get department from associated invoice."""
        return self.invoice.department if self.invoice else None
    
    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount}"
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['payment_id']),
            models.Index(fields=['invoice', 'status']),
            models.Index(fields=['processed_by']),
        ]


class Subscription(ABACModelMixin, models.Model):
    """Subscription model with ABAC support."""
    
    STATUS_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]
    
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    subscription_id = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='subscriptions')
    department = models.CharField(max_length=100, blank=True)
    plan_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='trial')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    next_billing_date = models.DateField(null=True, blank=True)
    trial_end_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_subscriptions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # ABAC configuration
    ABAC_POLICIES = {
        'view': 'subscription_view',
        'edit': 'subscription_edit',
        'delete': 'billing_admin_only',
        'cancel': 'subscription_cancel',
        'renew': 'subscription_renew'
    }
    
    # Use ABAC-enabled manager
    objects = ABACManager()
    
    def save(self, *args, **kwargs):
        # Copy department from customer if not set
        if not self.department and self.customer:
            self.department = self.customer.department
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Subscription {self.subscription_id} - {self.customer.name}"
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription_id']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['department']),
            models.Index(fields=['created_by']),
        ]