#!/usr/bin/env python3
"""Check what HTML is being returned for dashboard."""

import requests
from bs4 import BeautifulSoup

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings()

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
    
    # Access dashboard
    dashboard_url = "https://website.vfservices.viloforge.com/dashboard/"
    cookies = {"vf_jwt_token": token}
    
    response = requests.get(dashboard_url, cookies=cookies, verify=False)
    
    if response.status_code == 200:
        # Save full HTML to file
        with open('/tmp/dashboard.html', 'w') as f:
            f.write(response.text)
        print("✓ Dashboard HTML saved to /tmp/dashboard.html")
        
        # Parse and check menu
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find sidebar menu
        sidebar = soup.find('nav', class_='sidebar-menu')
        if sidebar:
            print("\n✓ Found sidebar menu")
            
            # Check if empty message is shown
            empty_msg = sidebar.find('p', class_='menu-empty')
            if empty_msg:
                print(f"  ⚠️  Empty message shown: {empty_msg.text}")
            
            # Check for menu list
            menu_list = sidebar.find('ul', class_='menu-list')
            if menu_list:
                items = menu_list.find_all('li', class_='menu-item', recursive=False)
                print(f"  Menu items found: {len(items)}")
            else:
                print("  ✗ No menu list found")
            
            # Check debug info
            debug_div = sidebar.find('div', class_='menu-debug')
            if debug_div:
                print(f"\n  Debug info: {debug_div.text.strip()}")
                
            # Print raw sidebar HTML
            print("\n  Raw sidebar HTML (first 500 chars):")
            print(str(sidebar)[:500])
        else:
            print("✗ No sidebar menu found in HTML")
    else:
        print(f"✗ Dashboard request failed: {response.status_code}")
else:
    print(f"✗ Login failed: {response.status_code}")