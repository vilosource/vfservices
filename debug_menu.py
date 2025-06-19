#!/usr/bin/env python3
"""Debug menu API response."""

import requests
import json
from pprint import pprint

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

# Login as alice
print("Logging in as alice...")
login_url = "https://identity.vfservices.viloforge.com/api/login/"
response = requests.post(
    login_url,
    json={"username": "alice", "password": "alice123"},
    verify=False
)

if response.status_code == 200:
    token = response.json()['token']
    print(f"✓ Got token: {token[:20]}...\n")
    
    # Get menu from API
    print("Fetching menu from inventory API...")
    menu_url = "https://inventory.vfservices.viloforge.com/api/menus/sidebar_menu/"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(menu_url, headers=headers, verify=False)
    
    if response.status_code == 200:
        menu_data = response.json()
        print("✓ Menu API Response:")
        print(f"  Permissions: {menu_data.get('user_permissions', [])}")
        print(f"\nMenu Items ({len(menu_data.get('items', []))}):")
        
        def print_menu_item(item, indent=0):
            prefix = "  " * indent + "- "
            print(f"{prefix}{item['label']} ({item.get('id', 'no-id')})")
            if 'children' in item:
                print(f"{'  ' * (indent + 1)}Children: {len(item['children'])}")
                for child in item['children']:
                    print_menu_item(child, indent + 2)
        
        for item in menu_data.get('items', []):
            print_menu_item(item)
            
        # Also show raw JSON for first item
        print("\n\nRaw JSON for first menu item:")
        if menu_data.get('items'):
            print(json.dumps(menu_data['items'][0], indent=2))
    else:
        print(f"✗ Menu API failed: {response.status_code}")
        print(response.text[:500])
else:
    print(f"✗ Login failed: {response.status_code}")