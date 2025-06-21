# User Dropdown Menu Customization Guide

This guide explains how to add custom menu items to the user dropdown menu in the website and cielo-website Django applications.

## Overview

Both `website` and `cielo-website` have user dropdown menus in their navigation bars that display when a logged-in user clicks on their username. This guide shows how to add new menu items, including role-based items that only appear for users with specific permissions.

## Template Locations

### Website
- **Template file**: `/website/templates/base.html`
- **Line numbers**: Look for the `dropdown-menu profile-dropdown` class (around line 125-142)

### Cielo-Website
- **Template file**: `/cielo_website/templates/base.html`
- **Line numbers**: Look for the `dropdown-menu profile-dropdown` class (around line 126-151)

## Basic Menu Structure

The dropdown menu follows this HTML structure:

```html
<div class="dropdown-menu dropdown-menu-end profile-dropdown">
    <!-- Header -->
    <div class="dropdown-header noti-title">
        <h6 class="text-overflow m-0">Welcome, {{ user.get_full_name|default:user.username }}!</h6>
    </div>
    
    <!-- Menu Items -->
    <a href="/accounts/profile/" class="dropdown-item notify-item">
        <i class="ri-account-circle-line"></i>
        <span>My Account</span>
    </a>
    
    <!-- Divider -->
    <div class="dropdown-divider"></div>
    
    <!-- More items... -->
</div>
```

## Adding a Simple Menu Item

To add a basic menu item that appears for all logged-in users:

1. Open the appropriate `base.html` file
2. Find the dropdown menu section
3. Add your menu item before the logout link:

```html
<a href="/your-path/" class="dropdown-item notify-item">
    <i class="ri-your-icon-class"></i>
    <span>Your Menu Label</span>
</a>
```

### Icon Classes
Both projects use RemixIcon. Common icons include:
- `ri-settings-3-line` - Settings
- `ri-admin-line` - Admin
- `ri-dashboard-line` - Dashboard
- `ri-file-list-line` - Reports
- `ri-team-line` - Teams
- `ri-shield-check-line` - Security

## Adding Role-Based Menu Items

To add menu items that only appear for users with specific roles:

### Step 1: Load the RBAC Template Tags

Add this at the top of the template file (after `{% load static %}`):

```django
{% load rbac_tags %}
```

### Step 2: Create the Template Tag File (if not exists)

Create `/webapp/templatetags/rbac_tags.py`:

```python
"""
Template tags for RBAC role checking.
"""
import sys
from pathlib import Path
from django import template
import logging

# Add common to path
common_path = Path(__file__).resolve().parent.parent.parent.parent / 'common'
if str(common_path) not in sys.path:
    sys.path.insert(0, str(common_path))

from rbac_abac.redis_client import get_user_attributes

register = template.Library()
logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def user_has_role(context, role_name, service_name=None):
    """
    Check if the current user has a specific role.
    
    For website: service_name defaults to 'website'
    For cielo_website: service_name defaults to 'cielo_website'
    """
    request = context.get('request')
    if not request or not hasattr(request, 'user') or not request.user.is_authenticated:
        return False
    
    # Set default service name based on the app
    if service_name is None:
        # Determine from module path
        module_path = Path(__file__).parent.parent.name
        service_name = 'cielo_website' if 'cielo' in module_path else 'website'
    
    try:
        user_attrs = get_user_attributes(request.user.id, service_name)
        if not user_attrs:
            return False
        
        return role_name in user_attrs.roles
        
    except Exception as e:
        logger.error(f"Error checking role {role_name}: {str(e)}", exc_info=True)
        return False
```

### Step 3: Add the Role-Based Menu Item

In the dropdown menu section:

```django
{% user_has_role 'admin_role_name' as has_admin_role %}
{% if has_admin_role %}
<div class="dropdown-divider"></div>
<a href="/admin-section/" class="dropdown-item notify-item">
    <i class="ri-admin-line"></i>
    <span>Admin Section</span>
</a>
{% endif %}
```

## Complete Example

Here's a complete example adding multiple role-based items:

```django
<!-- After Settings menu item -->
{% user_has_role 'identity_admin' as has_identity_admin %}
{% user_has_role 'billing_admin' as has_billing_admin %}
{% user_has_role 'reports_viewer' as has_reports %}

{% if has_identity_admin or has_billing_admin or has_reports %}
<div class="dropdown-divider"></div>
{% endif %}

{% if has_identity_admin %}
<a href="/admin/" class="dropdown-item notify-item">
    <i class="ri-admin-line"></i>
    <span>Identity Admin</span>
</a>
{% endif %}

{% if has_billing_admin %}
<a href="/billing/admin/" class="dropdown-item notify-item">
    <i class="ri-money-dollar-circle-line"></i>
    <span>Billing Admin</span>
</a>
{% endif %}

{% if has_reports %}
<a href="/reports/" class="dropdown-item notify-item">
    <i class="ri-file-chart-line"></i>
    <span>Reports</span>
</a>
{% endif %}
```

## Menu Item Order

Recommended order for menu items:
1. Welcome header
2. Profile/Account management items
3. Settings
4. Role-specific administrative items (with divider)
5. Logout (always last, with divider)

## Testing Your Changes

1. **Restart the container** after adding new template tags:
   ```bash
   docker compose restart website
   # or
   docker compose restart cielo-website
   ```

2. **Create a test** in `/playwright/{app-name}/smoke-tests/`:
   ```python
   def test_custom_menu_item(page: Page):
       """Test custom menu item appears for authorized users."""
       # Login as user with required role
       page.goto("https://website.vfservices.viloforge.com/accounts/login/")
       page.fill('input[name="email"]', 'test_user')
       page.fill('input[name="password"]', 'password')
       page.click('button[type="submit"]')
       
       # Open dropdown
       page.locator('.topbar-dropdown .nav-user').click()
       
       # Check menu item exists
       custom_item = page.locator('a.dropdown-item:has-text("Your Menu Label")')
       expect(custom_item).to_be_visible()
   ```

3. **Run the test**:
   ```bash
   pytest playwright/website/smoke-tests/test_your_menu.py -v -s
   ```

## Common Issues and Solutions

### Template Tag Not Found
- **Error**: `'rbac_tags' is not a registered tag library`
- **Solution**: 
  1. Ensure `__init__.py` exists in `/webapp/templatetags/`
  2. Restart the Django container
  3. Check that the file path is correct

### Menu Item Not Appearing
- **Possible causes**:
  1. User doesn't have the required role
  2. Template syntax error (check Django logs)
  3. Service name mismatch in role check
  4. Redis connection issues

### Icon Not Displaying
- **Solution**: Verify you're using a valid RemixIcon class. See [RemixIcon](https://remixicon.com/) for the full list.

## Best Practices

1. **Always test role-based items** with users that have and don't have the required roles
2. **Use meaningful role names** that clearly indicate the permission level
3. **Group related menu items** together with dividers
4. **Keep menu items concise** - use short, clear labels
5. **Document role requirements** in your code comments
6. **Create smoke tests** for all new menu items

## Role Management

To assign roles to users for testing:

```python
# Via Django shell
docker compose exec identity-provider python manage.py shell

from identity_app.models import User, Role, UserRole, Service
user = User.objects.get(username='testuser')
service = Service.objects.get(name='website')
role = Role.objects.get(name='your_role_name', service=service)
UserRole.objects.create(user=user, role=role)
```

## Related Documentation

- [RBAC System Overview](/dev-docs/rbac-system.md)
- [Identity Provider API](/identity-provider/docs/api.md)
- [Django Template Tags](https://docs.djangoproject.com/en/4.2/howto/custom-template-tags/)