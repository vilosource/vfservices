# Website Django App Structure

This directory contains the Django application for the website component of the vfservices project.

## Overview

The website Django app is structured as follows:

```mermaid
graph TD
    A[Website Django App] --> B[Project Configuration]
    A --> C[Webapp Application]
    A --> D[Authentication]
    A --> E[Logging]

    B --> B1[Settings: PostgreSQL, JWT]
    B --> B2[URL Routing]

    C --> C1[Views]
    C1 --> C1a[home: Public landing page]
    C1 --> C1b[private: JWT analysis]

    C --> C2[Templates]
    C2 --> C2a[index.html]
    C2 --> C2b[private.html]

    C --> C3[Middleware]
    C3 --> C3a[Request Logging]

    C --> C4[Utilities]
    C4 --> C4a[Logging Decorators]

    D --> D1[JWT Middleware]
    D --> D2[SSO Cookie]
    D --> D3[Login Required]

    E --> E1[Multiple Handlers]
    E --> E2[Custom Loggers]
    E --> E3[Error Tracking]
```

## Components

### Project Configuration (`main/`)

- **Settings**: Configure PostgreSQL database, JWT authentication, and other project settings
- **URL Routing**: Routes requests to the webapp views

### Webapp Application (`webapp/`)

- **Views**:
  - `home()`: Public landing page that renders `index.html`
  - `private()`: Authenticated endpoint for JWT analysis that renders `private.html`

- **Templates**:
  - `index.html`: Main landing page template
  - `private.html`: Template for displaying JWT user information and request details

- **Middleware**:
  - Custom request logging middleware

- **Utilities**:
  - Custom logging decorators and utilities

### Authentication

- Uses JWT middleware from the common package
- SSO cookie configuration
- `@login_required` decorator for protected views

### Logging

- Comprehensive logging configuration with multiple handlers
- Custom loggers for different components
- Error tracking and request logging

## Key Observations

1. The app is primarily focused on authentication analysis and request handling
2. No database models are currently defined
3. Comprehensive logging is implemented throughout
4. JWT authentication is handled through shared middleware
5. The app has two main views/templates

## Files

- `Dockerfile`: Docker configuration for the website service
- `entrypoint.sh`: Entry point script for Docker
- `manage.py`: Django project management script
- `main/`: Project configuration directory
- `webapp/`: Application directory with views, templates, and utilities
