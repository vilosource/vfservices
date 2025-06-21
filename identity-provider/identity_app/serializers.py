"""
Serializers for Identity Provider Admin API
"""
import json
from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Role, UserRole, Service, UserAttribute, ServiceAttribute


class RoleSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_display_name = serializers.CharField(source='service.display_name', read_only=True)
    user_count = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'display_name', 'description', 'is_global', 
                  'service_name', 'service_display_name', 'created_at', 'user_count']
        read_only_fields = ['id', 'created_at', 'user_count']


class UserRoleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    role_display_name = serializers.CharField(source='role.display_name', read_only=True)
    service_name = serializers.CharField(source='role.service.name', read_only=True)
    service_display_name = serializers.CharField(source='role.service.display_name', read_only=True)
    granted_by_username = serializers.CharField(source='granted_by.username', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRole
        fields = ['id', 'role_name', 'role_display_name', 'service_name', 
                  'service_display_name', 'granted_at', 'granted_by_username',
                  'expires_at', 'is_active']
        read_only_fields = ['id', 'granted_at', 'granted_by_username']
    
    def get_is_active(self, obj):
        return obj.is_active


class AssignRoleSerializer(serializers.Serializer):
    role_name = serializers.CharField()
    service_name = serializers.CharField()
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future")
        return value
    
    def validate(self, attrs):
        # Validate role and service exist
        try:
            service = Service.objects.get(name=attrs['service_name'])
            role = Role.objects.get(name=attrs['role_name'], service=service)
        except Service.DoesNotExist:
            raise serializers.ValidationError({"service_name": "Service not found"})
        except Role.DoesNotExist:
            raise serializers.ValidationError({"role_name": "Role not found for this service"})
        
        attrs['role'] = role
        attrs['service'] = service
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    roles_count = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                  'full_name', 'is_active', 'is_staff', 'is_superuser',
                  'date_joined', 'last_login', 'roles_count']
        read_only_fields = ['id', 'date_joined', 'last_login', 'is_staff', 'is_superuser']
    
    def get_roles_count(self, obj):
        return obj.user_roles.filter(
            expires_at__isnull=True
        ).count() + obj.user_roles.filter(
            expires_at__gt=timezone.now()
        ).count()
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserDetailSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name',
                  'full_name', 'is_active', 'is_staff', 'is_superuser',
                  'date_joined', 'last_login', 'roles']
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 
                           'is_staff', 'is_superuser']
    
    def get_roles(self, obj):
        active_roles = UserRole.objects.filter(
            user=obj
        ).select_related('role__service').order_by('-granted_at')
        return UserRoleSerializer(active_roles, many=True).data
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    initial_roles = AssignRoleSerializer(many=True, required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name',
                  'is_active', 'initial_roles']
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value
    
    def create(self, validated_data):
        initial_roles = validated_data.pop('initial_roles', [])
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Assign initial roles
        request_user = self.context.get('request').user
        for role_data in initial_roles:
            UserRole.objects.create(
                user=user,
                role=role_data['role'],
                granted_by=request_user,
                expires_at=role_data.get('expires_at')
            )
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'is_active']
    
    def validate_email(self, value):
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8)
    force_change = serializers.BooleanField(default=False)


class ServiceSerializer(serializers.ModelSerializer):
    role_count = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Service
        fields = ['id', 'name', 'display_name', 'description', 'manifest_version',
                  'is_active', 'registered_at', 'role_count', 'user_count']
        read_only_fields = ['id', 'registered_at']
    
    def get_role_count(self, obj):
        return obj.roles.count()
    
    def get_user_count(self, obj):
        return User.objects.filter(
            user_roles__role__service=obj,
            user_roles__expires_at__isnull=True
        ).distinct().count() + User.objects.filter(
            user_roles__role__service=obj,
            user_roles__expires_at__gt=timezone.now()
        ).distinct().count()


class BulkAssignRoleSerializer(serializers.Serializer):
    assignments = serializers.ListField(
        child=serializers.DictField(),
        min_length=1,
        max_length=100
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    
    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future")
        return value
    
    def validate_assignments(self, value):
        validated_assignments = []
        errors = []
        
        for idx, assignment in enumerate(value):
            try:
                # Validate required fields
                if 'user_id' not in assignment:
                    errors.append({idx: "user_id is required"})
                    continue
                if 'role_name' not in assignment:
                    errors.append({idx: "role_name is required"})
                    continue
                if 'service_name' not in assignment:
                    errors.append({idx: "service_name is required"})
                    continue
                
                # Validate user exists
                try:
                    user = User.objects.get(id=assignment['user_id'])
                except User.DoesNotExist:
                    errors.append({idx: f"User {assignment['user_id']} not found"})
                    continue
                
                # Validate role and service
                try:
                    service = Service.objects.get(name=assignment['service_name'])
                    role = Role.objects.get(name=assignment['role_name'], service=service)
                except Service.DoesNotExist:
                    errors.append({idx: f"Service {assignment['service_name']} not found"})
                    continue
                except Role.DoesNotExist:
                    errors.append({idx: f"Role {assignment['role_name']} not found for service"})
                    continue
                
                validated_assignments.append({
                    'user': user,
                    'role': role,
                    'service': service
                })
                
            except Exception as e:
                errors.append({idx: str(e)})
        
        if errors:
            raise serializers.ValidationError({"assignments": errors})
        
        return validated_assignments


class AuditLogSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    action = serializers.CharField()
    resource_type = serializers.CharField()
    resource_id = serializers.IntegerField(allow_null=True)
    changes = serializers.JSONField()
    ip_address = serializers.IPAddressField()
    user_agent = serializers.CharField()
    created_at = serializers.DateTimeField()


class UserAttributeSerializer(serializers.ModelSerializer):
    """Serializer for user attributes."""
    service_name = serializers.CharField(source='service.name', read_only=True, allow_null=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = UserAttribute
        fields = ['id', 'name', 'value', 'service', 'service_name', 
                  'updated_at', 'updated_by_username']
        read_only_fields = ['id', 'updated_at', 'updated_by_username']
    
    def validate_value(self, value):
        """Validate that value can be JSON serialized."""
        try:
            # Try to parse if it's a JSON string
            if isinstance(value, str) and value.startswith(('{', '[')):
                json.loads(value)
        except json.JSONDecodeError:
            # If it's not valid JSON, we'll store it as a plain string
            pass
        return value


class UserAttributeCreateUpdateSerializer(serializers.Serializer):
    """Serializer for creating/updating user attributes."""
    name = serializers.CharField(max_length=50)
    value = serializers.CharField()
    service_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_name(self, value):
        """Validate attribute name format."""
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Attribute name must start with lowercase letter and contain only "
                "lowercase letters, numbers, and underscores"
            )
        return value
    
    def validate_service_id(self, value):
        """Validate service exists."""
        if value is not None:
            try:
                Service.objects.get(id=value)
            except Service.DoesNotExist:
                raise serializers.ValidationError("Service not found")
        return value


class ServiceAttributeSerializer(serializers.ModelSerializer):
    """Serializer for service attribute definitions."""
    service_name = serializers.CharField(source='service.name', read_only=True)
    
    class Meta:
        model = ServiceAttribute
        fields = ['id', 'service', 'service_name', 'name', 'display_name', 
                  'description', 'attribute_type', 'is_required', 'default_value']
        read_only_fields = ['id']
    
    def validate_default_value(self, value):
        """Validate default value matches the attribute type."""
        if value:
            attribute_type = self.initial_data.get('attribute_type', 'string')
            try:
                # Validate JSON for complex types
                if attribute_type in ['json', 'list_string', 'list_integer']:
                    parsed = json.loads(value)
                    if attribute_type == 'list_string' and not isinstance(parsed, list):
                        raise serializers.ValidationError("Default value must be a list for list_string type")
                    if attribute_type == 'list_integer':
                        if not isinstance(parsed, list):
                            raise serializers.ValidationError("Default value must be a list for list_integer type")
                        # Check all items are integers
                        for item in parsed:
                            if not isinstance(item, int):
                                raise serializers.ValidationError("All items must be integers for list_integer type")
                elif attribute_type == 'integer':
                    int(value)
                elif attribute_type == 'boolean':
                    if value.lower() not in ['true', 'false', '1', '0']:
                        raise serializers.ValidationError("Default value must be true/false for boolean type")
            except (json.JSONDecodeError, ValueError) as e:
                raise serializers.ValidationError(f"Invalid default value for {attribute_type} type: {str(e)}")
        return value


class ServiceAttributeCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating service attribute definitions."""
    
    class Meta:
        model = ServiceAttribute
        fields = ['name', 'display_name', 'description', 'attribute_type', 
                  'is_required', 'default_value']
    
    def validate_name(self, value):
        """Validate attribute name format."""
        import re
        if not re.match(r'^[a-z][a-z0-9_]*$', value):
            raise serializers.ValidationError(
                "Attribute name must start with lowercase letter and contain only "
                "lowercase letters, numbers, and underscores"
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation."""
        # Validate default value if provided
        default_value = attrs.get('default_value')
        if default_value:
            serializer = ServiceAttributeSerializer()
            serializer.initial_data = attrs
            attrs['default_value'] = serializer.validate_default_value(default_value)
        return attrs


# Alias for backward compatibility
UserSerializer = UserListSerializer