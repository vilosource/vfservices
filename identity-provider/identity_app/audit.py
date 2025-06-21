"""
Audit logging for admin operations
"""
import logging
import json
from django.utils import timezone

logger = logging.getLogger('identity.audit')


def audit_log(user, action, resource_type, resource_id, changes, request=None):
    """
    Log an audit event
    
    Args:
        user: The user performing the action
        action: The action being performed (e.g., 'user_created', 'role_assigned')
        resource_type: Type of resource (e.g., 'user', 'role')
        resource_id: ID of the affected resource
        changes: Dict of changes made
        request: Optional request object for IP and user agent
    """
    
    log_data = {
        'timestamp': timezone.now().isoformat(),
        'user_id': user.id,
        'username': user.username,
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'changes': changes,
    }
    
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        
        log_data['ip_address'] = ip
        log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', 'unknown')
    
    # Log to file/system
    logger.info(f"AUDIT: {action}", extra={'audit_data': json.dumps(log_data)})
    
    # TODO: In future, save to database table for querying
    # AuditLog.objects.create(**log_data)