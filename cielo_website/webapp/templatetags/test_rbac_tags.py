"""
Test script to check if rbac_tags is working correctly.
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'main.settings')
django.setup()

from django.template import Context, Template
from django.test import RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a mock request
factory = RequestFactory()
request = factory.get('/')

# Get the admin user
try:
    user = User.objects.get(username='admin')
    request.user = user
    
    # Test the template tag
    template_str = """
    {% load rbac_tags %}
    {% user_has_role 'identity_admin' as has_admin_role %}
    Has identity_admin role: {{ has_admin_role }}
    """
    
    template = Template(template_str)
    context = Context({'request': request})
    result = template.render(context)
    
    print("Template rendering result:")
    print(result)
    
except User.DoesNotExist:
    print("Admin user not found")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()