#!/usr/bin/env python3
"""Debug menu API directly."""

import requests
import json

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

print("Debugging menu API...\n")

# Login as alice
login_url = "https://identity.vfservices.viloforge.com/api/login/"
response = requests.post(
    login_url,
    json={"username": "alice", "password": "alice123"},
    verify=False
)

if response.status_code == 200:
    token = response.json()['token']
    print("✓ Logged in as alice\n")
    
    # Try to access inventory menu API directly
    menu_url = "https://inventory.vfservices.viloforge.com/api/menu/sidebar_menu/"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Calling inventory menu API directly...")
    response = requests.get(menu_url, headers=headers, verify=False)
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        # Count items
        items = data.get('items', [])
        print(f"\nTotal items: {len(items)}")
        
        if items:
            for item in items:
                print(f"\nItem: {item.get('label', 'Unknown')}")
                if 'children' in item:
                    print(f"  Children: {len(item['children'])}")
                    for child in item['children'][:2]:
                        print(f"    - {child.get('label', 'Unknown')}")
                        if 'children' in child:
                            print(f"      (Has {len(child['children'])} sub-children)")
    else:
        print(f"Error: {response.text}")
else:
    print(f"✗ Login failed: {response.status_code}")