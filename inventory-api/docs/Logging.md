# Inventory-API Django Project Logging Documentation

## Introduction

The Inventory-API Django project implements a comprehensive logging solution designed for production API services with focus on inventory operations, security monitoring, and performance tracking. The logging system provides multiple log levels, specialized log files for different concerns, automatic API request tracking, and audit trail capabilities.

### Overall Configuration

The logging configuration is defined in `main/settings.py` and includes:

- **Log Base Directory**: Configurable via `LOG_BASE_DIR` environment variable (defaults to `/tmp`)

- **Multiple Log Files**:
  - `inventory_api.log` - General application logs (10MB max, 5 backups)
  - `inventory_api_debug.log` - Debug information (10MB max, 3 backups, only in DEBUG mode)
  - `inventory_api_errors.log` - Error-only logs (5MB max, 10 backups)
  - `inventory_api_requests.log` - API request logs (10MB max, 5 backups)
  - `inventory_api_security.log` - Security event logs (5MB max, 10 backups)

- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Formatters**: verbose, simple, detailed, api
- **Automatic Rotation**: Prevents log files from consuming excessive disk space

### Key Components

1. **Logging Utilities** (`inventory/logging_utils.py`):
   - `@log_api_request` decorator for automatic API endpoint logging
   - Specialized logging functions for inventory operations, security events, and performance metrics
   - StructuredLogger class for consistent logging
   - Pre-configured loggers: inventory_logger, api_logger, security_logger, operations_logger, audit_logger

2. **Configured Loggers**:
   - Django system loggers (django, django.request, django.security, django.db.backends)
   - App-specific loggers (inventory, inventory.views, inventory.models, inventory.api)
   - Specialized loggers (inventory.security, inventory.operations)
   - Authentication logger (common.jwt_auth)
   - REST Framework logger

## How to Add Logging to Django Apps

### 1. Import the Required Loggers

In your Django app's views, models, or any Python file:

```python
from inventory.logging_utils import (
    inventory_logger,
    api_logger,
    security_logger,
    operations_logger,
    audit_logger,
    log_inventory_operation,
    log_security_event,
    log_performance_metric,
    log_data_access
)
```

### 2. Use the API Request Decorator

For automatic API endpoint logging, use the `@log_api_request` decorator:

```python
from inventory.logging_utils import log_api_request
from rest_framework.decorators import api_view

@api_view(['POST'])
@log_api_request('create_item')
def create_inventory_item(request):
    # Your API logic here
    return Response({'status': 'success'})
```

This automatically logs:
- Request start with user context, IP, and endpoint name
- Request completion with status code
- Request duration (warns if >1 second)
- Any exceptions that occur

### 3. Log Inventory Operations

For inventory-specific operations, use the `log_inventory_operation` function:

```python
def update_stock(item_id, quantity, user):
    # Update stock logic
    item = InventoryItem.objects.get(id=item_id)
    old_quantity = item.quantity
    item.quantity = quantity
    item.save()
    
    # Log the operation
    log_inventory_operation(
        request=request,
        operation='stock_update',
        item_id=item_id,
        quantity_change=quantity - old_quantity,
        user_id=user.id,
        details={
            'old_quantity': old_quantity,
            'new_quantity': quantity,
            'reason': 'manual_adjustment'
        }
    )
    
    return item
```

### 4. Log Security Events

For security-related events, use the `log_security_event` function:

```python
def delete_item(request, item_id):
    if not request.user.has_perm('inventory.delete_item'):
        log_security_event(
            request=request,
            event_type='unauthorized_delete_attempt',
            severity='warning',
            details={
                'user_id': request.user.id,
                'item_id': item_id,
                'user_permissions': list(request.user.get_all_permissions())
            }
        )
        return Response({'error': 'Unauthorized'}, status=403)
    
    # Delete logic here
```

### 5. Log Performance Metrics

For performance monitoring, use the `log_performance_metric` function:

```python
import time

def generate_inventory_report(request):
    start_time = time.time()
    
    # Generate report logic
    report = compile_inventory_report()
    
    duration = time.time() - start_time
    log_performance_metric(
        request=request,
        metric_name='inventory_report_generation',
        value=duration,
        unit='seconds',
        details={
            'report_type': 'full_inventory',
            'item_count': report.item_count,
            'slow_operation': duration > 1.0
        }
    )
    
    return report
```

### 6. Log Data Access for Compliance

For audit and compliance purposes, use the `log_data_access` function:

```python
def export_inventory_data(request, format='csv'):
    # Check permissions
    if not request.user.has_perm('inventory.export_data'):
        return HttpResponseForbidden()
    
    # Log data access
    log_data_access(
        request=request,
        data_type='inventory_full_export',
        access_type='export',
        details={
            'format': format,
            'records_count': InventoryItem.objects.count(),
            'filters_applied': request.GET.dict()
        }
    )
    
    # Export logic
    data = export_to_format(format)
    return data
```

### 7. Use Structured Logging

For consistent structured logs across your app:

```python
from inventory.logging_utils import StructuredLogger

# Create a logger for your module
logger = StructuredLogger('inventory.warehouse')

def transfer_stock(from_warehouse, to_warehouse, item_id, quantity):
    logger.info('Stock transfer initiated', {
        'from_warehouse': from_warehouse.id,
        'to_warehouse': to_warehouse.id,
        'item_id': item_id,
        'quantity': quantity
    })
    
    try:
        # Transfer logic
        result = perform_transfer(from_warehouse, to_warehouse, item_id, quantity)
        logger.info('Stock transfer completed', {
            'transfer_id': result.id,
            'success': True
        })
        return result
    except InsufficientStockError as e:
        logger.error('Stock transfer failed', {
            'reason': 'insufficient_stock',
            'available': e.available_quantity,
            'requested': quantity
        }, exc_info=True)
        raise
```

### 8. Module-Level Logging

For general logging within modules:

```python
import logging

# Get module logger
logger = logging.getLogger(__name__)

class InventoryService:
    def process_batch_update(self, updates):
        logger.debug(f"Processing batch update with {len(updates)} items")
        
        successful = 0
        failed = 0
        
        for update in updates:
            try:
                self._update_item(update)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to update item {update['id']}: {str(e)}")
                failed += 1
        
        logger.info(f"Batch update completed: {successful} successful, {failed} failed")
        return {'successful': successful, 'failed': failed}
```

## Request Flow Tracking

The logging system enables tracking requests from start to end through several mechanisms:

### 1. Request Context

Every log entry from decorated endpoints includes:
- **User Information**: User ID, username (if authenticated)
- **Request Details**: HTTP method, path, query parameters
- **Client Information**: IP address (handles X-Forwarded-For), user agent
- **Timestamps**: ISO format timestamps for chronological ordering
- **Response Details**: Status code, duration

### 2. API Request Flow

The `@log_api_request` decorator tracks the complete request lifecycle:

```
1. Request arrives → Log entry: "API Request started: [endpoint_name]"
2. View processing → Your custom logs within the view
3. Response generation → Log entry: "API Request completed: [endpoint_name]"
4. Duration tracking → Warns if request takes >1 second
```

### 3. Following a Request

To follow a request through the logs:

1. **Filter by user**:
   ```bash
   grep "user_id.*123" /tmp/inventory_api*.log | sort -k2
   ```

2. **Filter by IP address**:
   ```bash
   grep "ip.*192.168.1.100" /tmp/inventory_api_requests.log
   ```

3. **Filter by endpoint**:
   ```bash
   grep "endpoint.*create_item" /tmp/inventory_api_requests.log
   ```

4. **Track inventory operations**:
   ```bash
   grep "operation.*stock_update" /tmp/inventory_api.log
   ```

5. **Monitor security events**:
   ```bash
   tail -f /tmp/inventory_api_security.log
   ```

### 4. Example Request Flow

Here's how a typical inventory API request appears in the logs:

```
# 1. Request arrives (inventory_api_requests.log)
2024-01-20 10:30:00,123 INFO [inventory.api] API Request started: update_stock - User: john_doe (123), IP: 192.168.1.100, Method: PUT, Path: /api/v1/items/456/stock

# 2. View processing (inventory_api.log)
2024-01-20 10:30:00,125 DEBUG [inventory.views] Updating stock for item 456, user has permissions: True

# 3. Inventory operation (inventory_api.log)
2024-01-20 10:30:00,150 INFO [inventory.operations] Inventory operation: stock_update - User: 123, Item: 456, Quantity change: -10, Details: {'old_quantity': 100, 'new_quantity': 90, 'reason': 'sale'}

# 4. Data access log (inventory_api.log)
2024-01-20 10:30:00,160 INFO [inventory.audit] Data access: inventory_item_update - User: 123, Access type: write, Details: {'item_id': 456, 'fields_modified': ['quantity']}

# 5. Performance metric (inventory_api.log)
2024-01-20 10:30:00,170 INFO [inventory.performance] Performance metric: stock_update_duration - Value: 0.045 seconds

# 6. Request completed (inventory_api_requests.log)
2024-01-20 10:30:00,175 INFO [inventory.api] API Request completed: update_stock - Status: 200, Duration: 0.052 seconds

# If slow (>1 second):
2024-01-20 10:30:02,000 WARNING [inventory.api] Slow API request detected: update_stock - Duration: 1.877 seconds
```

### 5. Debugging Tips

1. **Enable DEBUG logging** in development:
   ```python
   # In settings.py
   LOGGING['root']['level'] = 'DEBUG'
   ```

2. **Search logs efficiently**:
   ```bash
   # Find all errors for a specific item
   grep -E "ERROR.*item_id.*456" /tmp/inventory_api*.log
   
   # Find slow operations
   grep "slow_operation.*true" /tmp/inventory_api.log
   
   # Track stock changes
   grep "stock_update" /tmp/inventory_api.log | grep "item.*789"
   ```

3. **Add request IDs for better tracking**:
   ```python
   import uuid
   
   @api_view(['POST'])
   @log_api_request('bulk_update')
   def bulk_update(request):
       request_id = str(uuid.uuid4())
       logger = logging.getLogger(__name__)
       
       logger.info(f"Starting bulk update", extra={
           'request_id': request_id,
           'user_id': request.user.id,
           'items_count': len(request.data['items'])
       })
       
       # Process items with request_id
       for item in request.data['items']:
           process_item(item, request_id)
       
       logger.info(f"Bulk update completed", extra={
           'request_id': request_id
       })
   ```

4. **Create audit trails**:
   ```python
   def create_audit_trail(request, action, entity_type, entity_id, changes):
       audit_logger.info(f"Audit trail: {action}", extra={
           'user_id': request.user.id,
           'action': action,
           'entity_type': entity_type,
           'entity_id': entity_id,
           'changes': changes,
           'timestamp': timezone.now().isoformat(),
           'ip': get_client_ip(request)
       })
   ```

## Testing the Logging System

The project includes a comprehensive testing command:

```bash
python manage.py test_logging [--level LEVEL] [--logger LOGGER]
```

This command:
- Tests all configured loggers
- Verifies log file creation
- Tests utility functions
- Supports different log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Can test specific loggers

Examples:
```bash
# Test all loggers at INFO level
python manage.py test_logging

# Test with DEBUG level
python manage.py test_logging --level DEBUG

# Test specific logger
python manage.py test_logging --logger inventory.api
```

## Best Practices

1. **Use the appropriate logger** for your context:
   - `inventory_logger` for general inventory operations
   - `api_logger` for API-specific events
   - `security_logger` for security events
   - `operations_logger` for business operations
   - `audit_logger` for compliance and audit trails

2. **Include relevant context** in all log entries:
   - User ID for authenticated requests
   - Resource IDs (item_id, warehouse_id, etc.)
   - Operation results (success/failure)
   - Quantities and changes for inventory operations

3. **Use appropriate log levels**:
   - DEBUG: Detailed information for debugging
   - INFO: General informational messages
   - WARNING: Warning conditions (low stock, slow operations)
   - ERROR: Error conditions with stack traces
   - CRITICAL: Serious errors requiring immediate attention

4. **Structure your logs** for easy parsing:
   - Use consistent field names
   - Include all relevant IDs
   - Use the StructuredLogger for complex data

5. **Monitor inventory operations**:
   - Log all stock changes
   - Track data exports
   - Monitor bulk operations
   - Set up alerts for anomalies

6. **Security considerations**:
   - Never log sensitive data (passwords, tokens)
   - Use `log_security_event` for all security-related events
   - Monitor unauthorized access attempts
   - Track data access for compliance

## Log File Management

1. **Log Rotation**: Automatic via RotatingFileHandler
   - General logs: 10MB max, 5 backups
   - Debug logs: 10MB max, 3 backups
   - Error logs: 5MB max, 10 backups
   - Security logs: 5MB max, 10 backups

2. **Log Location**: Configurable via `LOG_BASE_DIR` environment variable

3. **Monitoring**: Set up monitoring for:
   - Error rate increases
   - Security events
   - Slow operations
   - Failed inventory operations

## Integration with Monitoring Systems

While not implemented by default, the logging system can be easily integrated with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- CloudWatch Logs
- Datadog
- Prometheus (via log parsing)

Consider adding:
- Centralized log aggregation
- Real-time alerting
- Log analytics and visualization
- Distributed tracing with correlation IDs
- Metrics extraction from logs