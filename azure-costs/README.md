# Azure Costs API

A Django REST API service for managing and tracking Azure cloud costs. This service is part of the VF Services ecosystem and integrates with the centralized identity provider for authentication and RBAC/ABAC authorization.

## Overview

The Azure Costs API provides endpoints for:
- Retrieving Azure cost data (future implementation)
- Budget tracking and alerts (future implementation)
- Cost analysis and reporting (future implementation)
- RBAC/ABAC integration for access control

Currently implemented endpoints:
- `/api/health` - Health check endpoint
- `/api/private` - Private endpoint requiring authentication
- `/api/test-rbac` - RBAC/ABAC testing endpoint

## Architecture

This service follows the same architecture patterns as other services in the VF Services ecosystem:
- Django REST Framework for API development
- JWT authentication via centralized identity provider
- PostgreSQL database for data persistence
- Redis for caching and session management
- Comprehensive logging system
- Docker containerization
- Traefik reverse proxy integration

## Requirements

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker and Docker Compose

## Local Development Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd vfservices/azure-costs
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

## Docker Deployment

### Using the main docker-compose.yml

The service is integrated into the main VF Services docker-compose.yml:

```bash
cd vfservices
docker compose up -d azure-costs
```

### Standalone deployment

To run the service independently:

```bash
cd azure-costs
docker compose up -d
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `POSTGRES_*` - PostgreSQL connection settings
- `REDIS_*` - Redis connection settings
- `VF_JWT_SECRET` - JWT secret for token validation
- `APPLICATION_SET_DOMAIN` - Domain for the service (default: cielo)
- `IDENTITY_PROVIDER_URL` - URL of the identity provider service

### Logging Configuration

The service uses a comprehensive logging system with multiple log files:
- `azure_costs.log` - General application logs
- `azure_costs_debug.log` - Debug logs (only in DEBUG mode)
- `azure_costs_errors.log` - Error logs
- `azure_costs_requests.log` - API request logs
- `azure_costs_security.log` - Security event logs

## API Documentation

### Health Check
```
GET /api/health
```
Returns service health status. No authentication required.

**Response:**
```json
{
    "status": "healthy",
    "service": "azure-costs-api",
    "version": "1.0.0",
    "timestamp": "2024-01-20T10:30:00Z"
}
```

### Private Endpoint
```
GET /api/private
Authorization: Bearer <JWT_TOKEN>
```
Returns user information. Requires authentication.

**Response:**
```json
{
    "message": "This is a private endpoint",
    "user": {
        "id": 123,
        "username": "john_doe",
        "email": "john@example.com"
    },
    "timestamp": "2024-01-20T10:30:00Z"
}
```

### RBAC Test
```
GET /api/test-rbac
Authorization: Bearer <JWT_TOKEN>
```
Tests RBAC/ABAC permissions.

**Response:**
```json
{
    "message": "RBAC test successful",
    "user_id": 123,
    "roles": ["user", "admin"],
    "attributes": {
        "department": "IT",
        "clearance_level": "high"
    },
    "has_access": true,
    "timestamp": "2024-01-20T10:30:00Z"
}
```

## Testing

### Run unit tests:
```bash
python manage.py test
```

### Test logging configuration:
```bash
python manage.py test_logging
```

### Test with specific log level:
```bash
python manage.py test_logging --level DEBUG
```

## Domain Access

The service is accessible via:
- Production: `https://azure-costs.cielo.viloforge.com`
- Local development: `http://localhost:8000`

## Security

- All endpoints except `/api/health` require JWT authentication
- JWT tokens are validated against the centralized identity provider
- RBAC/ABAC permissions are enforced based on user roles and attributes
- All security events are logged to dedicated security log files
- Sensitive data is automatically filtered from logs

## Future Enhancements

1. **Azure Cost Management Integration**:
   - Connect to Azure Cost Management API
   - Retrieve real-time cost data
   - Historical cost analysis

2. **Budget Management**:
   - Set and track budgets
   - Budget alerts and notifications
   - Cost forecasting

3. **Reporting Features**:
   - Cost breakdown by resource type
   - Department/project cost allocation
   - Custom report generation

4. **Cost Optimization**:
   - Recommendations for cost savings
   - Resource utilization analysis
   - Automated cost optimization actions

## Contributing

1. Follow the existing code patterns and structure
2. Ensure all new endpoints have appropriate logging
3. Add comprehensive tests for new features
4. Update documentation as needed

## Support

For issues or questions, please contact the development team or create an issue in the repository.