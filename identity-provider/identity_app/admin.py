from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Service, Role, UserRole, ServiceAttribute, 
    UserAttribute, ServiceManifest
)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for Service model."""
    list_display = ['name', 'display_name', 'is_active', 'registered_at', 'updated_at']
    list_filter = ['is_active', 'registered_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['registered_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Status', {
            'fields': ('is_active', 'manifest_version')
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    """Admin interface for Role model."""
    list_display = ['name', 'service', 'display_name', 'is_global', 'created_at']
    list_filter = ['service', 'is_global', 'created_at']
    search_fields = ['name', 'display_name', 'description', 'service__name']
    readonly_fields = ['created_at', 'updated_at', 'full_name']
    
    fieldsets = (
        (None, {
            'fields': ('service', 'name', 'display_name', 'description')
        }),
        ('Configuration', {
            'fields': ('is_global', 'full_name')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with service data."""
        return super().get_queryset(request).select_related('service')


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Admin interface for UserRole model."""
    list_display = ['user', 'role', 'resource_id', 'is_active_status', 'granted_at', 'expires_at']
    list_filter = ['role__service', 'granted_at', 'expires_at']
    search_fields = ['user__username', 'user__email', 'role__name', 'resource_id']
    readonly_fields = ['granted_at', 'is_expired', 'is_active']
    autocomplete_fields = ['user', 'role', 'granted_by']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'role', 'resource_id')
        }),
        ('Assignment Details', {
            'fields': ('granted_by', 'granted_at', 'expires_at')
        }),
        ('Status', {
            'fields': ('is_active', 'is_expired'),
            'classes': ('collapse',)
        }),
    )
    
    def is_active_status(self, obj):
        """Display active status with color coding."""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        else:
            return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related(
            'user', 'role', 'role__service', 'granted_by'
        )


@admin.register(ServiceAttribute)
class ServiceAttributeAdmin(admin.ModelAdmin):
    """Admin interface for ServiceAttribute model."""
    list_display = ['name', 'service', 'display_name', 'attribute_type', 'is_required']
    list_filter = ['service', 'attribute_type', 'is_required']
    search_fields = ['name', 'display_name', 'description', 'service__name']
    
    fieldsets = (
        (None, {
            'fields': ('service', 'name', 'display_name', 'description')
        }),
        ('Configuration', {
            'fields': ('attribute_type', 'is_required', 'default_value')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with service data."""
        return super().get_queryset(request).select_related('service')


@admin.register(UserAttribute)
class UserAttributeAdmin(admin.ModelAdmin):
    """Admin interface for UserAttribute model."""
    list_display = ['user', 'attribute_display', 'value_preview', 'updated_at', 'updated_by']
    list_filter = ['service', 'updated_at']
    search_fields = ['user__username', 'user__email', 'name', 'value']
    readonly_fields = ['updated_at', 'get_value']
    autocomplete_fields = ['user', 'service', 'updated_by']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'service', 'name', 'value')
        }),
        ('Metadata', {
            'fields': ('updated_at', 'updated_by', 'get_value'),
            'classes': ('collapse',)
        }),
    )
    
    def attribute_display(self, obj):
        """Display attribute with service namespace."""
        service_str = f"{obj.service.name}:" if obj.service else "global:"
        return f"{service_str}{obj.name}"
    attribute_display.short_description = 'Attribute'
    
    def value_preview(self, obj):
        """Show truncated value preview."""
        value_str = str(obj.value)
        if len(value_str) > 50:
            return f"{value_str[:50]}..."
        return value_str
    value_preview.short_description = 'Value'
    
    def get_queryset(self, request):
        """Optimize queryset with related data."""
        return super().get_queryset(request).select_related(
            'user', 'service', 'updated_by'
        )


@admin.register(ServiceManifest)
class ServiceManifestAdmin(admin.ModelAdmin):
    """Admin interface for ServiceManifest model."""
    list_display = ['service', 'version', 'is_active', 'submitted_at', 'submitted_by_ip']
    list_filter = ['service', 'is_active', 'submitted_at']
    search_fields = ['service__name', 'manifest_data']
    readonly_fields = ['submitted_at', 'formatted_manifest']
    
    fieldsets = (
        (None, {
            'fields': ('service', 'version', 'is_active')
        }),
        ('Manifest Data', {
            'fields': ('formatted_manifest',)
        }),
        ('Submission Details', {
            'fields': ('submitted_at', 'submitted_by_ip'),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_manifest(self, obj):
        """Display formatted JSON manifest."""
        import json
        if obj.manifest_data:
            formatted = json.dumps(obj.manifest_data, indent=2)
            return format_html('<pre style="max-height: 400px; overflow-y: scroll;">{}</pre>', formatted)
        return "No manifest data"
    formatted_manifest.short_description = 'Manifest Data'
    
    def get_queryset(self, request):
        """Optimize queryset with service data."""
        return super().get_queryset(request).select_related('service')
    
    def has_add_permission(self, request):
        """Prevent manual manifest creation - should be done via API."""
        return False