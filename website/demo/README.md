# VF Services RBAC-ABAC Demo Application

This demo application provides an interactive interface to explore and test the Role-Based and Attribute-Based Access Control (RBAC-ABAC) system implemented across VF Services microservices.

## Features

### 1. **Demo Dashboard** (`/demo/`)
- Overview of the RBAC-ABAC system
- Introduction to all demo users and their roles
- Setup instructions and quick start guide

### 2. **RBAC Dashboard** (`/demo/rbac/`)
- View current user's roles and attributes
- Compare expected vs actual permissions
- Live permission testing against API endpoints
- Real-time display of Redis-cached attributes

### 3. **API Explorer** (`/demo/api-explorer/`)
- Interactive API endpoint testing
- Test any endpoint across all services
- View request/response details
- See how authentication affects access

### 4. **Permission Matrix** (`/demo/permissions/`)
- Visual grid showing all users and their assigned roles
- Dynamic display based on actual database data
- Shows which services are registered
- Attribute-based restrictions overview

### 5. **Interactive Playground** (`/demo/playground/`)
- Pre-built scenarios for each demo user
- Step-by-step access control demonstrations
- Custom API testing interface
- Real-world use case examples

## Setup Instructions

### 1. Start All Services

Ensure all microservices are running:
```bash
docker-compose up -d
```

### 2. Initialize Demo Users

Run the management command to create demo users with their roles and attributes:

```bash
cd identity-provider
python manage.py setup_demo_users --reset
```

This creates four demo users:
- **alice** (password: password123) - Senior Manager
- **bob** (password: password123) - Billing Specialist
- **charlie** (password: password123) - Cloud Infrastructure Manager
- **david** (password: password123) - Customer Service Representative

### 3. Access the Demo

Navigate to: `http://website.vfservices.viloforge.com/demo/`

## Demo Users Overview

### Alice - Senior Manager
- **Roles**: billing_admin, inventory_manager, customer_manager
- **Access**: Can manage billing operations up to $50,000, manage resources in regions 1 & 2
- **Department**: Management

### Bob - Billing Specialist
- **Roles**: invoice_manager, payment_processor, invoice_sender, stock_viewer
- **Access**: Can create invoices up to $5,000, process payments, view inventory
- **Department**: Finance

### Charlie - Cloud Infrastructure Manager
- **Roles**: warehouse_manager, stock_adjuster, movement_approver, count_supervisor
- **Access**: Full control over region 1 (us-east-1) resources only
- **Department**: Operations

### David - Customer Service Representative
- **Roles**: invoice_viewer, payment_viewer, product_viewer, stock_viewer
- **Access**: Read-only access, limited to customer 100
- **Department**: Support

## Key Features

### User Switcher
- Quick switch between demo users
- Maintains session state
- Shows current user context

### Live API Testing
- Make real API calls to all services
- See actual permission checks in action
- View detailed error messages for denied access

### Permission Visualization
- Color-coded permission status
- Expected vs actual comparison
- Real-time updates from Redis cache

## Technical Implementation

The demo app integrates with the actual RBAC-ABAC system:

1. **Uses Real Models**: Queries actual Service, Role, UserRole, and UserAttribute models
2. **Redis Integration**: Displays cached user attributes from Redis
3. **JWT Authentication**: Uses the same JWT tokens as the production system
4. **Live API Calls**: Makes actual HTTP requests to service endpoints

## Troubleshooting

### No Roles Showing
- Ensure services are running and have registered their manifests
- Run `setup_demo_users` command to create roles

### Authentication Issues
- Check that the identity provider is running
- Verify JWT middleware is properly configured

### Permission Denied
- Check the Permission Matrix to verify role assignments
- Ensure Redis is running and caching is working
- Verify service manifests are properly registered

## Development

To extend the demo:

1. Add new scenarios in `views.py`
2. Update templates in `templates/demo/`
3. Add new demo users in `setup_demo_users.py`

The demo app is designed to be a living documentation of the RBAC-ABAC system, helping developers understand and test access control patterns.