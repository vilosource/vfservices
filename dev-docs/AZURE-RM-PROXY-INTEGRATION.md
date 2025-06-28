# Azure Resource Manager Proxy Integration Guide

## Overview
The Azure RM Proxy Server provides a REST API interface for querying Azure resources with intelligent caching. It's integrated into the VF Services platform and accessible at https://arm-proxy.maltacentral.com.

## Architecture

### Components
- **FastAPI Application**: Modern Python web framework for the API
- **Redis Cache**: Distributed caching for Azure API responses
- **Azure SDK**: Official Azure libraries for resource management
- **Traefik**: Reverse proxy handling SSL and routing

### Key Features
- Efficient caching to reduce Azure API calls
- RESTful API with automatic documentation
- Support for multiple Azure resource types
- Mock mode for testing without Azure connection
- Health checks and monitoring endpoints

## Accessing the Service

### API Documentation
The service provides interactive API documentation:
- **Swagger UI**: https://arm-proxy.maltacentral.com/docs
- **ReDoc**: https://arm-proxy.maltacentral.com/redoc
- **OpenAPI Schema**: https://arm-proxy.maltacentral.com/openapi.json

**Important**: The documentation is at `/docs`, NOT `/api/docs`

### Health Check
Verify the service is running:
```bash
curl https://arm-proxy.maltacentral.com/api/ping
```

## API Endpoints

### Subscriptions
List all Azure subscriptions:
```bash
GET /api/subscriptions/
```

### Resource Groups
List resource groups in a subscription:
```bash
GET /api/subscriptions/{subscription_id}/resource-groups/
```

### Virtual Machines
List VMs in a resource group:
```bash
GET /api/subscriptions/{subscription_id}/resource-groups/{resource_group}/virtual-machines/
```

Get specific VM details:
```bash
GET /api/subscriptions/{subscription_id}/resource-groups/{resource_group}/virtual-machines/{vm_name}
```

### Additional Endpoints
- `/api/routes/` - Network routes
- `/api/vm-reports/` - VM reports with detailed information
- `/api/vm-hostnames/` - VM hostname mappings
- `/api/vnet-peering/` - Virtual network peering information

## Configuration

### Environment Variables
The service is configured through environment variables in docker-compose.yml:

```yaml
azure-rm-proxy:
  environment:
    # Port configuration
    - PORT=7890
    
    # Redis cache settings
    - CACHE_TYPE=redis
    - REDIS_URL=redis://redis:6379/2
    
    # Logging
    - LOG_LEVEL=INFO
    
    # Performance
    - MAX_CONCURRENCY=10
    
    # Azure credentials (from host environment)
    - AZURE_TENANT_ID=${AZURE_TENANT_ID}
    - AZURE_CLIENT_ID=${AZURE_CLIENT_ID}
    - AZURE_CLIENT_SECRET=${AZURE_CLIENT_SECRET}
    
    # Testing
    - USE_MOCK=${USE_MOCK:-false}
```

### Azure Authentication
The service uses Azure's DefaultAzureCredential which tries authentication methods in this order:
1. Environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
2. Managed Identity (if running in Azure)
3. Azure CLI credentials
4. Other configured methods

### Cache Configuration
- **Type**: Redis (can be changed to memory or none)
- **Default TTL**: 1 hour
- **Database**: Redis database 2 (to avoid conflicts)
- **Refresh**: Add `?refresh=true` to any endpoint to bypass cache

## Development

### Running Locally
1. Set Azure credentials in environment:
   ```bash
   export AZURE_TENANT_ID=your-tenant-id
   export AZURE_CLIENT_ID=your-client-id
   export AZURE_CLIENT_SECRET=your-client-secret
   ```

2. Build and start the service:
   ```bash
   docker compose build azure-rm-proxy
   docker compose up -d azure-rm-proxy
   ```

3. Check logs:
   ```bash
   docker compose logs -f azure-rm-proxy
   ```

### Mock Mode
For testing without Azure connection:
```bash
USE_MOCK=true docker compose up -d azure-rm-proxy
```

This uses test fixtures from the `infra-data` directory.

### Debugging
1. Check service health:
   ```bash
   curl https://arm-proxy.maltacentral.com/api/ping
   ```

2. View container logs:
   ```bash
   docker compose logs azure-rm-proxy
   ```

3. Access container shell:
   ```bash
   docker compose exec azure-rm-proxy /bin/bash
   ```

## Security Considerations

### Current State (Phase 1)
- Service is publicly accessible (no authentication)
- Uses HTTPS via Traefik
- Runs as non-root user in container
- Azure credentials secured via environment variables

### Planned Security (Phase 2)
- JWT authentication integration with identity-provider
- Role-based access control (RBAC)
- Rate limiting
- Audit logging
- Service-to-service authentication

## Monitoring

### Health Checks
- Docker health check: `/api/ping` every 30 seconds
- Traefik monitors service availability
- Container auto-restarts on failure

### Logs
- Application logs: `./azure-rm-proxy-server/logs/`
- Container logs: `docker compose logs azure-rm-proxy`
- Log level configurable via LOG_LEVEL environment variable

## Troubleshooting

### Common Issues

1. **404 on /api/docs**
   - Use `/docs` instead of `/api/docs`
   - FastAPI serves documentation at the root, not under /api

2. **Authentication Errors**
   - Verify Azure credentials are set in environment
   - Check credentials have necessary permissions
   - Try with Azure CLI: `az login` first

3. **Cache Issues**
   - Add `?refresh=true` to force cache bypass
   - Check Redis is running: `docker compose ps redis`
   - Monitor Redis: `docker compose exec redis redis-cli`

4. **SSL Certificate Errors**
   - Ensure arm-proxy.maltacentral.com is in certificate
   - Run: `make certbot-renew` if needed
   - Restart Traefik: `docker compose restart traefik`

## API Usage Examples

### List All Subscriptions
```bash
curl -X GET "https://arm-proxy.maltacentral.com/api/subscriptions/" \
  -H "accept: application/json"
```

### Get VMs in a Resource Group
```bash
curl -X GET "https://arm-proxy.maltacentral.com/api/subscriptions/{sub_id}/resource-groups/{rg_name}/virtual-machines/" \
  -H "accept: application/json"
```

### Force Cache Refresh
```bash
curl -X GET "https://arm-proxy.maltacentral.com/api/subscriptions/?refresh=true" \
  -H "accept: application/json"
```

## Future Enhancements

### Phase 2 - Authentication & Security
- JWT token validation
- Integration with identity-provider
- Role-based access control
- API key support for automation

### Phase 3 - Monitoring & Operations
- Prometheus metrics
- Grafana dashboards
- Centralized logging
- Alert configuration

### Phase 4 - Advanced Features
- WebSocket support for real-time updates
- Batch operations
- Export capabilities (CSV, Excel)
- Admin UI for management

## Maintenance

### Updating the Service
1. Update code in `azure-rm-proxy-server/`
2. Rebuild: `docker compose build azure-rm-proxy`
3. Restart: `docker compose up -d azure-rm-proxy`

### Updating Dependencies
1. Edit `azure-rm-proxy-server/requirements.txt`
2. Rebuild the container
3. Test thoroughly

### Backup Considerations
- Redis cache is ephemeral (can be rebuilt)
- No persistent data storage required
- Configuration in docker-compose.yml should be version controlled

---

*Last Updated: 2025-01-28*  
*Changelog: Initial documentation for Phase 1 integration*