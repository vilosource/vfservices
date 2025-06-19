#!/usr/bin/env python3
"""Check Redis cache for menu data."""

import redis
import json
import subprocess

try:
    # Try connecting through Docker
    print("Checking Redis cache for menu data...\n")
    
    # Get all keys
    result = subprocess.run(
        ['docker', 'exec', 'vfservices-redis-1', 'redis-cli', 'KEYS', 'menu:*'],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        keys = result.stdout.strip().split('\n')
        if keys and keys[0]:
            print(f"Found {len(keys)} menu cache entries:\n")
            
            for key in keys:
                print(f"Key: {key}")
                
                # Get the value
                get_result = subprocess.run(
                    ['docker', 'exec', 'vfservices-redis-1', 'redis-cli', 'GET', key],
                    capture_output=True,
                    text=True
                )
                
                if get_result.returncode == 0:
                    try:
                        # Parse and pretty print the JSON
                        menu_data = json.loads(get_result.stdout)
                        print(f"  Menu: {menu_data.get('menu_name', 'Unknown')}")
                        print(f"  Items: {len(menu_data.get('items', []))}")
                        
                        # Show first item structure
                        if menu_data.get('items'):
                            first_item = menu_data['items'][0]
                            print(f"  First item: {first_item.get('label', 'Unknown')}")
                            if 'children' in first_item:
                                print(f"    - Has {len(first_item['children'])} children")
                                for child in first_item['children'][:3]:  # Show first 3
                                    print(f"      - {child.get('label', 'Unknown')}")
                                    if 'children' in child:
                                        print(f"        (Has {len(child['children'])} sub-children)")
                        
                        # Get TTL
                        ttl_result = subprocess.run(
                            ['docker', 'exec', 'vfservices-redis-1', 'redis-cli', 'TTL', key],
                            capture_output=True,
                            text=True
                        )
                        if ttl_result.returncode == 0:
                            ttl = int(ttl_result.stdout.strip())
                            if ttl > 0:
                                print(f"  TTL: {ttl} seconds ({ttl//60} minutes)")
                            else:
                                print(f"  TTL: No expiration")
                                
                    except json.JSONDecodeError:
                        print(f"  Value: {get_result.stdout[:100]}... (not JSON)")
                
                print()
        else:
            print("No menu cache entries found in Redis")
    else:
        print(f"Error checking Redis: {result.stderr}")
        
    # Also check for user attributes which might affect menu
    print("\n\nChecking for user attributes in cache:")
    attr_result = subprocess.run(
        ['docker', 'exec', 'vfservices-redis-1', 'redis-cli', 'KEYS', 'user_attrs:*'],
        capture_output=True,
        text=True
    )
    
    if attr_result.returncode == 0:
        attr_keys = attr_result.stdout.strip().split('\n')
        if attr_keys and attr_keys[0]:
            print(f"Found {len(attr_keys)} user attribute entries")
            # Show first few
            for key in attr_keys[:3]:
                print(f"  - {key}")
        else:
            print("No user attribute entries found")
            
except Exception as e:
    print(f"Error: {e}")