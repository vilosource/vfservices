# Django Template Best Practices for VF Services

This guide covers important best practices when working with Django templates in the VF Services ecosystem.

## Template Inheritance

### Critical: Preserving Parent Block Content

When extending a base template and overriding blocks, especially JavaScript blocks, you must be careful to preserve parent content when needed.

#### ❌ Common Mistake - Losing Parent JavaScript

```django
{# In child template - THIS WILL BREAK AVATAR LOADING! #}
{% extends "base.html" %}

{% block extra_js %}
<script src="{% static 'my-page-script.js' %}"></script>
{% endblock %}
```

This completely replaces the parent's `extra_js` block, which means any JavaScript from `base.html` (like avatar-management.js) will NOT be loaded.

#### ✅ Correct Approach - Include Parent Content

```django
{# In child template - This preserves avatar and other base functionality #}
{% extends "base.html" %}

{% block extra_js %}
{{ block.super }}  {# This includes all parent JavaScript first #}
<script src="{% static 'my-page-script.js' %}"></script>
{% endblock %}
```

### Real-World Example: Profile Page Issue

We discovered this issue on the profile page where avatars weren't loading because the template was overriding the `extra_js` block without including `{{ block.super }}`.

**Before (Broken):**
```django
{% block extra_js %}
<script src="{% static 'assets/js/identity-api-client.js' %}"></script>
{% endblock %}
```

**After (Fixed):**
```django
{% block extra_js %}
{{ block.super }}  {# Now avatar-management.js loads! #}
<script src="{% static 'assets/js/identity-api-client.js' %}"></script>
{% endblock %}
```

### Avatar Implementation Across Projects

All three Django applications now use the same pattern for avatar management:

**website/templates/base.html:**
```django
{% block extra_js %}
{{ block.super }}
<!-- Avatar Management -->
<script src="{% static 'js/avatar-management.js' %}"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        AvatarManager.config.identityProviderUrl = 'https://identity.vfservices.viloforge.com';
        {% if user.is_authenticated %}
        AvatarManager.init('.user-avatar');
        {% endif %}
    });
</script>
{% endblock %}
```

This same pattern is used in:
- `cielo-website/templates/base.html`
- `maltacentral-web/templates/base.html`

## Avatar Display Guidelines

### Base Template Integration

All templates that extend `base.html` automatically get avatar functionality if they follow these rules:

1. **Don't override `extra_js` block without `{{ block.super }}`**
2. **Use the CSS class `user-avatar` on avatar img elements**
3. **Ensure user is authenticated before initializing avatar loading**

### Avatar Element Structure

```html
<!-- Standard avatar element in navigation -->
<img src="{% static 'assets/images/users/avatar-1.jpg' %}" 
     alt="user" 
     class="rounded-circle user-avatar">
```

The JavaScript will automatically:
- Find all elements with class `user-avatar`
- Fetch the user's avatar URL from Identity Provider
- Update the `src` attribute
- Fall back to numbered defaults if no custom avatar exists

## JavaScript Loading Order

### Understanding Block Hierarchy

```
page.html (root template)
    └── {% block base_js %}     [Core vendor libraries]
    └── {% block extra_js %}    [Empty by default]

base.html (extends page.html)
    └── {% block base_js %}
            {{ block.super }}   [Includes vendor libraries]
            [Dashboard specific libraries]
        {% endblock %}
    └── {% block extra_js %}
            {{ block.super }}   [Usually empty from page.html]
            [Avatar management script]
            [Other base functionality]
        {% endblock %}

your-template.html (extends base.html)
    └── {% block extra_js %}
            {{ block.super }}   [CRITICAL: Include this!]
            [Your page-specific scripts]
        {% endblock %}
```

## Common Patterns

### Adding Page-Specific JavaScript

```django
{% extends "base.html" %}

{% block extra_js %}
{{ block.super }}

<!-- Page configuration -->
<script>
    window.PAGE_CONFIG = {
        apiUrl: "{{ api_url }}",
        refreshInterval: 30000
    };
</script>

<!-- Page-specific libraries -->
<script src="{% static 'libs/chart.js' %}"></script>

<!-- Page logic -->
<script src="{% static 'js/my-page.js' %}"></script>
{% endblock %}
```

### Conditional JavaScript Loading

```django
{% block extra_js %}
{{ block.super }}

{% if user.is_authenticated %}
    <script src="{% static 'js/authenticated-features.js' %}"></script>
{% endif %}

{% if debug %}
    <script src="{% static 'js/debug-tools.js' %}"></script>
{% endif %}
{% endblock %}
```

## Debugging Tips

### Check If Scripts Are Loading

1. Open browser DevTools
2. Go to Network tab
3. Filter by JS
4. Reload page
5. Verify these are loaded in order:
   - vendor.min.js
   - app.min.js
   - avatar-management.js
   - Your page scripts

### Console Checks

```javascript
// Check if AvatarManager is available
console.log(typeof AvatarManager !== 'undefined');

// Check configuration
console.log(AvatarManager.config);

// Manually trigger avatar loading
AvatarManager.init('.user-avatar');
```

## Testing Template Changes

When modifying templates that extend base.html:

1. **Test avatar display** - Ensure avatars still load
2. **Check console for errors** - No JavaScript errors
3. **Verify script loading order** - Base scripts load first
4. **Test on multiple pages** - Ensure consistency

### Playwright Test Example

```python
def test_javascript_loading_order(page):
    """Ensure base JavaScript loads before page scripts."""
    page.goto("https://website.vfservices.viloforge.com/your-page/")
    
    # Check AvatarManager is loaded
    assert page.evaluate("typeof AvatarManager !== 'undefined'")
    
    # Check your page script loaded after
    assert page.evaluate("typeof YourPageModule !== 'undefined'")
```

## References

- [User Management Architecture](./user-management-architecture.md)
- [JWT Authentication Guide](./JWT-AUTHENTICATION-GUIDE.md)
- [Django Template Documentation](https://docs.djangoproject.com/en/stable/topics/templates/)

---
*Last Updated: 2025-06-22T09:30:00Z - Initial documentation covering template inheritance and avatar integration issues*