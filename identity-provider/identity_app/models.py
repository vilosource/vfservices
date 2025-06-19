from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
import json


class Service(models.Model):
    """
    Represents a registered microservice in the system.
    
    Services register themselves by submitting a manifest that declares
    their roles and required user attributes.
    """
    name = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex='^[a-z][a-z0-9_-]*$',
                message='Service name must start with lowercase letter and contain only lowercase letters, numbers, hyphens, and underscores'
            )
        ],
        help_text='Unique service identifier (e.g., billing_api, inventory_api)'
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Human-readable service name'
    )
    description = models.TextField(
        blank=True,
        help_text='Service description'
    )
    manifest_version = models.CharField(
        max_length=20,
        default='1.0',
        help_text='Version of the manifest schema'
    )
    registered_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the service was first registered'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the service manifest was last updated'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the service is currently active'
    )
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"


class Role(models.Model):
    """
    Represents a role within a service.
    
    Roles are namespaced by service and can be either global
    (applying to the entire service) or scoped to specific resources.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='roles',
        help_text='Service this role belongs to'
    )
    name = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex='^[a-z][a-z0-9_]*$',
                message='Role name must start with lowercase letter and contain only lowercase letters, numbers, and underscores'
            )
        ],
        help_text='Role identifier (e.g., admin, editor, viewer)'
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Human-readable role name'
    )
    description = models.TextField(
        blank=True,
        help_text='What this role allows users to do'
    )
    is_global = models.BooleanField(
        default=True,
        help_text='If True, role applies to entire service. If False, can be scoped to resources.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = [['service', 'name']]
        ordering = ['service', 'name']
        indexes = [
            models.Index(fields=['service', 'name']),
        ]
    
    def __str__(self):
        return f"{self.service.name}:{self.name}"
    
    @property
    def full_name(self):
        """Get the full role name including service namespace."""
        return f"{self.service.name}_{self.name}"


class UserRole(models.Model):
    """
    Assignment of a role to a user.
    
    Can optionally be scoped to a specific resource within the service.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_roles',
        help_text='User who has this role'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_assignments',
        help_text='Role assigned to the user'
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Optional: Specific resource ID this role applies to (for scoped roles)'
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='roles_granted',
        help_text='User who granted this role'
    )
    granted_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the role was granted'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Optional: When this role assignment expires'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'role']),
            models.Index(fields=['user', 'role', 'resource_id']),
            models.Index(fields=['expires_at']),
        ]
        # Prevent duplicate role assignments
        unique_together = [['user', 'role', 'resource_id']]
    
    def __str__(self):
        scope = f" (resource: {self.resource_id})" if self.resource_id else ""
        return f"{self.user.username} has {self.role}{scope}"
    
    @property
    def is_expired(self):
        """Check if this role assignment has expired."""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def is_active(self):
        """Check if this role assignment is currently active."""
        return not self.is_expired and self.role.service.is_active


class ServiceAttribute(models.Model):
    """
    Defines custom attributes that a service uses for ABAC decisions.
    
    These are declared in the service manifest and indicate what
    user attributes the service needs for its policies.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='attributes',
        help_text='Service that uses this attribute'
    )
    name = models.CharField(
        max_length=50,
        validators=[
            RegexValidator(
                regex='^[a-z][a-z0-9_]*$',
                message='Attribute name must start with lowercase letter and contain only lowercase letters, numbers, and underscores'
            )
        ],
        help_text='Attribute identifier (e.g., department, clearance_level)'
    )
    display_name = models.CharField(
        max_length=100,
        help_text='Human-readable attribute name'
    )
    description = models.TextField(
        blank=True,
        help_text='What this attribute represents and how it\'s used'
    )
    attribute_type = models.CharField(
        max_length=20,
        choices=[
            ('string', 'String'),
            ('integer', 'Integer'),
            ('boolean', 'Boolean'),
            ('list_string', 'List of Strings'),
            ('list_integer', 'List of Integers'),
            ('json', 'JSON Object'),
        ],
        default='string',
        help_text='Data type of the attribute'
    )
    is_required = models.BooleanField(
        default=False,
        help_text='Whether all users must have this attribute for this service'
    )
    default_value = models.TextField(
        blank=True,
        null=True,
        help_text='Default value if not set (JSON encoded)'
    )
    
    class Meta:
        unique_together = [['service', 'name']]
        ordering = ['service', 'name']
    
    def __str__(self):
        return f"{self.service.name}:{self.name}"
    
    def get_default_value(self):
        """Parse and return the default value."""
        if self.default_value:
            try:
                return json.loads(self.default_value)
            except json.JSONDecodeError:
                return self.default_value
        return None


class UserAttribute(models.Model):
    """
    Stores custom attribute values for users.
    
    These attributes are used by services for ABAC decisions.
    Global attributes apply across all services, while service-specific
    attributes only apply to that service.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='custom_attributes',
        help_text='User this attribute belongs to'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='user_attributes',
        help_text='Service this attribute is for (null = global attribute)'
    )
    name = models.CharField(
        max_length=50,
        help_text='Attribute name'
    )
    value = models.TextField(
        help_text='Attribute value (JSON encoded for complex types)'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When this attribute was last updated'
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='attributes_updated',
        help_text='User who last updated this attribute'
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'service', 'name']),
            models.Index(fields=['user', 'name']),
        ]
        # Each user can only have one value per attribute per service
        unique_together = [['user', 'service', 'name']]
    
    def __str__(self):
        service_str = f"{self.service.name}:" if self.service else "global:"
        return f"{self.user.username} - {service_str}{self.name}"
    
    def get_value(self):
        """Parse and return the attribute value."""
        try:
            return json.loads(self.value)
        except json.JSONDecodeError:
            return self.value
    
    def set_value(self, value):
        """Set the attribute value, JSON encoding if necessary."""
        if isinstance(value, (dict, list)):
            self.value = json.dumps(value)
        else:
            self.value = str(value)


class ServiceManifest(models.Model):
    """
    Stores the complete manifest submitted by a service.
    
    Keeps history of all manifests for audit purposes.
    """
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='manifests',
        help_text='Service this manifest belongs to'
    )
    version = models.IntegerField(
        help_text='Manifest version number (incremented on each update)'
    )
    manifest_data = models.JSONField(
        help_text='Complete manifest JSON data'
    )
    submitted_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this manifest was submitted'
    )
    submitted_by_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address that submitted the manifest'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this is the currently active manifest'
    )
    
    class Meta:
        ordering = ['-version']
        indexes = [
            models.Index(fields=['service', 'is_active']),
            models.Index(fields=['service', 'version']),
        ]
        unique_together = [['service', 'version']]
    
    def __str__(self):
        return f"{self.service.name} manifest v{self.version}"