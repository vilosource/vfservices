# Identity Provider API Documentation

## Overview

The Identity Provider API is a Django-based authentication service that provides JWT token management for the VF Services platform. It handles user authentication, token generation, and serves as the central identity management system for all services in the platform.

## Base URL

- **Production**: `https://identity.vfservices.viloforge.com`
- **Development**: `http://localhost:8100`

## Interactive Documentation

The API provides interactive documentation through Swagger UI and ReDoc:

- **Swagger UI**: `/api/docs/` - Interactive API documentation with request/response examples
- **ReDoc**: `/api/redoc/` - Alternative documentation format
- **OpenAPI Schema**: `/api/schema/` - Raw OpenAPI/Swagger schema in JSON format

### HTTPS Schema Selection

The Swagger UI at `/api/docs/` allows you to select between HTTP and HTTPS protocols using the schema dropdown in the top-right corner of the interface. This is particularly useful when testing the API in different environments.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require a valid JWT token in the Authorization header.

### Header Format
```
Authorization: Bearer <jwt_token>
```

### Obtaining a Token

Use the `/api/login/` endpoint to obtain a JWT token by providing valid credentials.

## API Endpoints

### 1. API Information

#### GET `/api/`

Get general information about the API and available endpoints.

**Authentication**: None required

**Response**:
```json
{
  "service": "Identity Provider API",
  "version": "1.0.0",
  "description": "Authentication and JWT token management service",
  "endpoints": {
    "/api/": {
      "method": "GET",
      "description": "Get API information",
      "authentication": "None"
    },
    "/api/login/": {
      "method": "POST",
      "description": "Authenticate user and obtain JWT token",
      "authentication": "None",
      "parameters": {
        "username": "string (required)",
        "password": "string (required)"
      },
      "returns": {
        "token": "JWT token string"
      }
    },
    "/api/status/": {
      "method": "GET",
      "description": "API health check and status",
      "authentication": "None"
    }
  },
  "authentication": {
    "type": "JWT Token",
    "description": "Use the token obtained from /api/login/ in the Authorization header",
    "header_format": "Authorization: Bearer <token>"
  },
  "timestamp": "2025-06-15T10:30:00.000Z"
}
```

### 2. User Authentication

#### POST `/api/login/`

Authenticate a user and obtain a JWT token.

**Authentication**: None required

**Request Body**:
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Parameters**:
- `username` (string, required): User's username or email
- `password` (string, required): User's password

**Response**:

**Success (200)**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Error Responses**:

**400 Bad Request** - Missing credentials:
```json
{
  "detail": "Username and password are required"
}
```

**400 Bad Request** - Invalid request format:
```json
{
  "detail": "Invalid request format"
}
```

**401 Unauthorized** - Invalid credentials:
```json
{
  "detail": "Invalid credentials"
}
```

**500 Internal Server Error** - Server error:
```json
{
  "detail": "Authentication system error"
}
```

### 3. API Status

#### GET `/api/status/`

Check the health and status of the API service.

**Authentication**: None required

**Response**:
```json
{
  "status": "healthy",
  "service": "identity-provider",
  "version": "1.0.0",
  "timestamp": "2025-06-15T10:30:00.000Z"
}
```

## Web Interface Endpoints

The service also provides web-based authentication interfaces:

### 1. Index Page

#### GET `/`

Main landing page for the identity provider service.

**Response**: HTML page with service information

### 2. Login Page

#### GET `/login/`
#### POST `/login/`

Web-based login interface for users.

**GET**: Displays login form
**POST**: Processes login form submission and sets authentication cookies

**Parameters** (POST):
- `username`: User's username or email
- `password`: User's password
- `redirect_uri` (optional): URL to redirect after successful login

## JWT Token Structure

The JWT tokens issued by this service contain the following claims:

```json
{
  "username": "user@example.com",
  "email": "user@example.com",
  "iat": 1718442600,
  "exp": 1718529000
}
```

**Claims**:
- `username`: User's username
- `email`: User's email address
- `iat`: Issued at timestamp
- `exp`: Expiration timestamp

## CORS Configuration

The API is configured to handle CORS (Cross-Origin Resource Sharing) requests from the following origins:

- `https://identity.vfservices.viloforge.com`
- `http://identity.vfservices.viloforge.com`
- `http://localhost:8000`
- `http://127.0.0.1:8000`
- `http://127.0.0.1:8100`

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses:

### Common Error Codes

- **400 Bad Request**: Invalid request format or missing required parameters
- **401 Unauthorized**: Invalid credentials or missing authentication
- **403 Forbidden**: Access denied
- **404 Not Found**: Endpoint not found
- **500 Internal Server Error**: Server-side error

### Error Response Format

```json
{
  "detail": "Error description message"
}
```

## Rate Limiting

Currently, no rate limiting is implemented, but it's recommended to implement rate limiting in production environments to prevent abuse.

## Security Considerations

1. **HTTPS Only**: Use HTTPS in production environments
2. **Token Security**: Store JWT tokens securely on the client side
3. **Token Expiration**: Tokens have a limited lifetime for security
4. **Credential Protection**: Never log or expose user passwords
5. **CORS**: Properly configure CORS origins for your environment

## Example Usage

### Using curl

#### Get API Information
```bash
curl -X GET "https://identity.vfservices.viloforge.com/api/"
```

#### Login and Get Token
```bash
curl -X POST "https://identity.vfservices.viloforge.com/api/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "password123"
  }'
```

#### Check API Status
```bash
curl -X GET "https://identity.vfservices.viloforge.com/api/status/"
```

### Using JavaScript (fetch)

```javascript
// Login and get token
async function login(username, password) {
  try {
    const response = await fetch('https://identity.vfservices.viloforge.com/api/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,
        password: password
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      return data.token;
    } else {
      const error = await response.json();
      throw new Error(error.detail);
    }
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

// Use token for authenticated requests
async function makeAuthenticatedRequest(token, url) {
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  return response.json();
}
```

### Using Python (requests)

```python
import requests

# Login and get token
def login(username, password):
    url = "https://identity.vfservices.viloforge.com/api/login/"
    data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(url, json=data)
    
    if response.status_code == 200:
        return response.json()["token"]
    else:
        raise Exception(f"Login failed: {response.json()['detail']}")

# Use token for authenticated requests
def make_authenticated_request(token, url):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    return response.json()

# Example usage
try:
    token = login("user@example.com", "password123")
    print(f"Token obtained: {token}")
    
    # Use token for other API calls
    # result = make_authenticated_request(token, "https://other-service.com/api/")
    
except Exception as e:
    print(f"Error: {e}")
```

## Development and Testing

### Running Locally

1. Start the development server:
```bash
cd identity-provider
python manage.py runserver 0.0.0.0:8100
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8100/api/docs/
   - ReDoc: http://localhost:8100/api/redoc/

### Running Tests

```bash
cd identity-provider
python manage.py test
```

## Support

For issues and questions regarding the Identity Provider API, please check:

1. **Interactive Documentation**: Use the Swagger UI at `/api/docs/` for real-time API testing
2. **Server Logs**: Check application logs for detailed error information
3. **Health Check**: Use `/api/status/` to verify service availability

## Version History

- **v1.0.0**: Initial release with JWT authentication, interactive documentation, and CORS support
