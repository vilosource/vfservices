# Inventory API - Logging Setup

This document describes the comprehensive logging configuration for the Inventory API service.

## Overview

The Inventory API has a structured logging system that captures inventory operations, stock changes, and business events:
- Inventory operations (add, remove, update stock)
- API requests and responses
- Stock level changes and alerts
- Security events
- Performance metrics

## Log Configuration

### Log Files

The log directory is configurable through the `LOG_BASE_DIR` environment variable (defaults to `/tmp/`):

```bash
# Default setup
python manage.py runserver  # logs to /tmp/

# Production setup
export LOG_BASE_DIR=/var/log/inventory
python manage.py runserver  # logs to /var/log/inventory/

# Testing with custom directory
LOG_BASE_DIR=/custom/logs python manage.py test_logging --skip-checks
```

The following log files are created in the configured directory:

- **inventory.log** - General application logs
- **inventory_debug.log** - Debug level logs (development only)
- **inventory_error.log** - Error and critical logs
- **inventory_api.log** - API request/response logs
- **inventory_security.log** - Security-related events
- **inventory_operations.log** - Inventory operation logs

### Log Levels

The logging configuration supports all standard Python logging levels:
- `DEBUG` - Detailed diagnostic information
- `INFO` - General information about inventory operations
- `WARNING` - Low stock alerts and unusual patterns
- `ERROR` - Operation errors and failures
- `CRITICAL` - System failures affecting inventory

### Loggers

The following loggers are configured:

- `inventory` - Main application logger
- `inventory.api` - API-specific logs
- `inventory.security` - Security events
- `inventory.performance` - Performance metrics
- `inventory.operations` - Inventory operations
- `django.request` - Django request handling
- `django.security` - Django security events

## Logging Utilities

### Available Functions

#### `log_api_request(endpoint_name)`
Decorator for logging API endpoint access and performance.

```python
@log_api_request('get_inventory')
@api_view(['GET'])
def get_inventory(request):
    return Response(inventory_data)
```

#### `log_inventory_operation(operation_type, user, item_id, quantity, extra_data)`
Log inventory operations with detailed context.

```python
log_inventory_operation(
    operation_type='stock_update',
    user=request.user,
    item_id='ITEM001',
    quantity=50,
    extra_data={'reason': 'restock', 'supplier': 'SUPP001'}
)
```

#### `log_security_event(event_type, request, user, severity, extra_data)`
Log security-related events.

```python
log_security_event(
    event_type='unauthorized_access_attempt',
    request=request,
    severity='WARNING',
    extra_data={'attempted_item': 'ITEM001'}
)
```

#### `log_performance_metric(operation, duration, extra_data)`
Log performance metrics for inventory operations.

```python
log_performance_metric(
    operation='bulk_stock_update',
    duration=2.34,
    extra_data={'items_processed': 1000}
)
```

#### `log_stock_alert(item_id, current_stock, threshold, alert_type)`
Log stock level alerts.

```python
log_stock_alert(
    item_id='ITEM001',
    current_stock=5,
    threshold=10,
    alert_type='low_stock'
)
```

### StructuredLogger Class

The `StructuredLogger` class provides consistent logging interface:

```python
from inventory.logging_utils import StructuredLogger

logger = StructuredLogger('inventory.custom')
logger.info('Operation completed', item_id='ITEM001', quantity=100)
logger.warning('Low stock detected', item_id='ITEM002', current_stock=3)
```

## Testing Logging

### Management Command

Test the logging configuration using the management command:

```bash
# Test basic logging (default directory)
python manage.py test_logging --skip-checks

# Test with custom log directory
LOG_BASE_DIR=/custom/logs python manage.py test_logging --skip-checks

# Test all loggers with custom directory
LOG_BASE_DIR=/var/log/inventory python manage.py test_logging --all-loggers --skip-checks

# Test specific log level
python manage.py test_logging --level debug --skip-checks
```

### Manual Testing

```python
import logging
from inventory.logging_utils import log_inventory_operation

# Test standard logging
logger = logging.getLogger('inventory')
logger.info('Test message')

# Test utility functions
log_inventory_operation(
    operation_type='test_operation',
    item_id='TEST001',
    quantity=1
)
```

## Inventory Operation Categories

### Stock Operations
- `stock_add` - Items added to inventory
- `stock_remove` - Items removed from inventory
- `stock_update` - Stock quantity updated
- `stock_transfer` - Items transferred between locations
- `stock_adjustment` - Manual stock adjustments

### Item Operations
- `item_create` - New item created
- `item_update` - Item information updated
- `item_delete` - Item removed from system
- `item_activate` - Item activated
- `item_deactivate` - Item deactivated

### Supplier Operations
- `supplier_create` - New supplier added
- `supplier_update` - Supplier information updated
- `supplier_order` - Order placed with supplier
- `supplier_delivery` - Delivery received from supplier

### Alert Events
- `low_stock` - Stock below minimum threshold
- `out_of_stock` - Item out of stock
- `overstock` - Stock above maximum threshold
- `expiry_warning` - Items approaching expiry date

## Best Practices

### 1. Operation Logging
Log all inventory operations with full context:

```python
# Stock updates
log_inventory_operation(
    operation_type='stock_update',
    user=request.user,
    item_id=item.id,
    quantity=new_quantity,
    extra_data={
        'previous_quantity': old_quantity,
        'reason': 'customer_order',
        'order_id': order.id
    }
)
```

### 2. API Request Logging
Use decorators for consistent API logging:

```python
@log_api_request('inventory_search')
@api_view(['GET'])
def search_inventory(request):
    # Implementation
    pass
```

### 3. Stock Alert Logging
Log stock level alerts for monitoring:

```python
# Check stock levels
if current_stock <= low_stock_threshold:
    log_stock_alert(
        item_id=item.id,
        current_stock=current_stock,
        threshold=low_stock_threshold,
        alert_type='low_stock'
    )
```

### 4. Performance Monitoring
Log performance for critical operations:

```python
start_time = time.time()
# ... perform bulk operation
duration = time.time() - start_time

log_performance_metric(
    operation='bulk_inventory_import',
    duration=duration,
    extra_data={'items_processed': len(items)}
)
```

### 5. Error Handling
Include comprehensive error logging:

```python
try:
    # Inventory operation
    pass
except ValidationError as e:
    logger.error(
        'Inventory validation failed',
        extra={
            'item_id': item_id,
            'error': str(e),
            'user': str(request.user)
        }
    )
    raise
```

## Monitoring and Alerting

### Stock Level Monitoring
- Monitor low stock alerts
- Track out-of-stock events
- Alert on unusual stock movements
- Monitor expiry date warnings

### Performance Monitoring
- Track API response times
- Monitor bulk operation performance
- Alert on slow database queries
- Track system resource usage

### Business Metrics
- Monitor inventory turnover
- Track supplier performance
- Alert on unusual order patterns
- Monitor cost variations

### Security Monitoring
- Track unauthorized access attempts
- Monitor sensitive operation logs
- Alert on suspicious activities
- Log privilege escalations

## API Endpoint Logging

### Request Logging
All API endpoints automatically log:
- Request method and path
- User information
- Client IP address
- Request timestamp
- Response status code
- Response time

### Response Logging
API responses include:
- Success/failure status
- Error messages (if any)
- Data modification details
- Performance metrics

## Inventory Audit Trail

### Operation Tracking
The logging system maintains a complete audit trail:
- Who performed the operation
- When the operation occurred
- What was changed
- Why the change was made (if provided)
- System state before and after

### Compliance Support
Audit trails support compliance with:
- Financial regulations (inventory valuation)
- Tax requirements (stock movements)
- Industry standards (traceability)
- Internal policies (authorization)

## Configuration Details

The logging configuration is defined in `inventory-api/main/settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'inventory_formatter': {
            'format': '{levelname} {asctime} [INVENTORY] {module} {message}',
            'style': '{',
        },
        'api_formatter': {
            'format': '{levelname} {asctime} [API] {module} {message}',
            'style': '{',
        },
        'operations_formatter': {
            'format': '{levelname} {asctime} [OPS] {module} {message}',
            'style': '{',
        },
    },
    # ... handlers and loggers configuration
}
```

## Advanced Features

### Structured Data Logging
Use structured logging for complex inventory data:

```python
logger.info('Inventory batch processed', extra={
    'batch_id': batch.id,
    'items_processed': len(items),
    'success_count': success_count,
    'error_count': error_count,
    'processing_time': duration,
    'user_id': user.id,
    'timestamp': timezone.now().isoformat()
})
```

### Contextual Logging
Include relevant business context:

```python
# In inventory views
logger.debug('Processing inventory request', extra={
    'request_id': request_id,
    'user': str(request.user),
    'warehouse': warehouse.name,
    'operation_type': operation_type,
    'item_count': len(items)
})
```

### Custom Log Filters
Implement custom filters for specific needs:

```python
class InventoryFilter(logging.Filter):
    def filter(self, record):
        # Custom filtering logic
        return True
```

## Integration with External Systems

### ERP System Integration
Log integration events with ERP systems:

```python
log_inventory_operation(
    operation_type='erp_sync',
    extra_data={
        'erp_system': 'SAP',
        'sync_type': 'full',
        'records_synced': 1500,
        'sync_duration': 45.2
    }
)
```

### Warehouse Management Systems
Log WMS integration:

```python
log_inventory_operation(
    operation_type='wms_update',
    extra_data={
        'wms_system': 'Oracle WMS',
        'location_updates': 50,
        'stock_adjustments': 25
    }
)
```

## Troubleshooting

### Common Issues

1. **Missing operation logs**: Check function calls and decorators
2. **Performance log gaps**: Verify timing measurement code
3. **Alert logs not appearing**: Check threshold configurations
4. **API logs incomplete**: Verify middleware and decorators

### Debug Mode

Enable debug logging for troubleshooting:

```python
LOGGING['loggers']['inventory']['level'] = 'DEBUG'
LOGGING['loggers']['inventory.operations']['level'] = 'DEBUG'
```

### Log Analysis

For investigation:
1. Check operation logs for transaction history
2. Review API logs for request patterns
3. Analyze performance logs for bottlenecks
4. Correlate security logs with operations

## Production Recommendations

### Log Management
- Implement log rotation
- Use centralized logging
- Set up log archiving
- Monitor disk space usage

### Security
- Secure log file access
- Encrypt sensitive log data
- Implement log integrity checks
- Regular security log reviews

### Performance
- Optimize log I/O performance
- Use asynchronous logging for high-volume operations
- Implement log sampling for very frequent events
- Monitor logging overhead

### Monitoring
- Set up real-time alerting
- Create dashboards for key metrics
- Implement automated log analysis
- Regular performance reviews
