# Azure Costs API Project Plan

## Overview
Create a new Django REST API project called `azure-costs` that follows the same patterns and structure as the `billing-api` project. This service will be responsible for managing and tracking Azure cloud costs and will be accessible via the domain `azure-costs.cielo`.

## Project Structure
```
azure-costs/
├── main/                      # Main Django app (settings, urls, wsgi)
│   ├── __init__.py
│   ├── settings.py           # Django settings (based on billing-api)
│   ├── urls.py               # Root URL configuration
│   ├── wsgi.py               # WSGI application
│   └── asgi.py               # ASGI application
├── azure_costs/              # Core application app
│   ├── __init__.py
│   ├── models.py             # Data models for Azure costs
│   ├── views.py              # API views
│   ├── urls.py               # App-specific URLs
│   ├── serializers.py        # DRF serializers
│   ├── permissions.py        # Custom permissions
│   ├── logging_utils.py      # Logging utilities (based on billing-api)
│   └── management/
│       └── commands/
│           └── test_logging.py
├── common/                   # Shared utilities
│   └── jwt_auth/            # JWT authentication (copy from billing-api)
│       ├── __init__.py
│       ├── middleware.py
│       └── authentication.py
├── docs/
│   ├── Plan.md              # This file
│   ├── API.md               # API documentation
│   └── Logging.md           # Logging documentation
├── requirements.txt         # Python dependencies
├── manage.py               # Django management script
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment variables example
└── README.md               # Project documentation
```

## Implementation Steps

### 1. Django Project Setup
- Create Django project with `django-admin startproject main .`
- Create azure_costs app with `python manage.py startapp azure_costs`
- Copy common/jwt_auth from billing-api project

### 2. Settings Configuration (based on billing-api)
- Configure Django settings following billing-api patterns
- Set up environment variables for configuration
- Configure CORS settings
- Configure REST Framework settings
- Configure logging based on billing-api pattern
- Configure static and media files
- Set up database configuration (PostgreSQL)

### 3. API Endpoints Implementation

#### `/api/health` - Health Check Endpoint
- Public endpoint (no authentication required)
- Returns service status and basic information
- Response format:
  ```json
  {
    "status": "healthy",
    "service": "azure-costs-api",
    "version": "1.0.0",
    "timestamp": "2024-01-20T10:30:00Z"
  }
  ```

#### `/api/private` - Private Endpoint
- Requires JWT authentication
- Returns user information and authentication details
- Response format:
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

#### `/api/test-rbac` - RBAC Test Endpoint
- Requires JWT authentication
- Tests RBAC/ABAC permissions
- Checks user roles and attributes from JWT
- Response format:
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

### 4. Authentication & Authorization
- Implement JWT authentication middleware (copy from billing-api)
- Configure authentication classes in REST Framework
- Set up permission classes for endpoints
- Integrate with identity-provider service for token validation

### 5. Logging Configuration
- Create logging_utils.py based on billing-api pattern
- Implement structured logging
- Configure log files:
  - azure_costs.log (general)
  - azure_costs_debug.log (debug)
  - azure_costs_errors.log (errors)
  - azure_costs_requests.log (API requests)
  - azure_costs_security.log (security events)
- Implement @log_api_request decorator
- Create test_logging management command

### 6. Docker Configuration
- Create Dockerfile based on billing-api
- Configure docker-compose.yml with:
  - Azure Costs service
  - PostgreSQL database
  - Redis for caching
  - Integration with existing Traefik network
- Set up health checks

### 7. Traefik Configuration
- Configure labels for Traefik routing
- Set up domain: azure-costs.cielo
- Configure HTTPS with Let's Encrypt
- Set up middleware for headers and CORS

### 8. Environment Configuration
- Create .env.example with all required variables:
  - DATABASE_URL
  - REDIS_URL
  - SECRET_KEY
  - DEBUG
  - ALLOWED_HOSTS
  - CORS_ALLOWED_ORIGINS
  - IDENTITY_PROVIDER_URL
  - LOG_BASE_DIR

### 9. Testing
- Create unit tests for API endpoints
- Test JWT authentication
- Test RBAC functionality
- Test logging functionality
- Create Playwright smoke tests

### 10. Documentation
- Create comprehensive README.md
- Document API endpoints in API.md
- Create Logging.md based on other projects
- Include setup and deployment instructions

## Key Features to Implement

### From billing-api pattern:
1. **Structured Logging**: Comprehensive logging with multiple handlers and formatters
2. **JWT Authentication**: Middleware for validating JWT tokens from identity-provider
3. **CORS Support**: Proper CORS configuration for frontend integration
4. **Health Monitoring**: Health check endpoint for service monitoring
5. **Error Handling**: Consistent error response format
6. **API Versioning**: URL-based versioning (/api/v1/)
7. **Environment-based Configuration**: All settings configurable via environment variables
8. **Docker Support**: Full containerization with docker-compose
9. **Traefik Integration**: Reverse proxy configuration with automatic HTTPS

### Security Considerations:
1. JWT token validation on all protected endpoints
2. RBAC/ABAC integration for fine-grained permissions
3. Security event logging
4. Rate limiting (future enhancement)
5. Input validation and sanitization

### Performance Considerations:
1. Redis caching for frequently accessed data
2. Database query optimization
3. Asynchronous task processing (future enhancement)
4. Response compression
5. Pagination for list endpoints

## Dependencies (requirements.txt)
```
Django==4.2.7
djangorestframework==3.14.0
django-cors-headers==4.3.0
python-decouple==3.8
psycopg2-binary==2.9.9
redis==5.0.1
django-redis==5.4.0
PyJWT==2.8.0
cryptography==41.0.7
gunicorn==21.2.0
python-json-logger==2.0.7
```

## Success Criteria
1. All three API endpoints working correctly
2. JWT authentication functioning properly
3. RBAC test endpoint correctly reading user roles/attributes
4. Comprehensive logging implemented
5. Docker container builds and runs successfully
6. Service accessible via azure-costs.cielo domain through Traefik
7. Health checks passing
8. Follows billing-api patterns and best practices

## Future Enhancements
1. Add actual Azure cost tracking models and endpoints
2. Implement cost analysis and reporting features
3. Add webhook support for cost alerts
4. Implement data synchronization with Azure Cost Management API
5. Add dashboard API endpoints
6. Implement cost optimization recommendations