#!/usr/bin/env python3
"""Clear menu cache from Redis."""

import redis
import sys

try:
    # Connect to Redis
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    
    # Get all keys matching menu pattern
    menu_keys = r.keys('menu:*')
    
    if menu_keys:
        print(f"Found {len(menu_keys)} menu cache entries")
        for key in menu_keys:
            print(f"  Deleting: {key}")
            r.delete(key)
        print("✓ Menu cache cleared successfully")
    else:
        print("No menu cache entries found")
        
    # Also try to clear Django cache
    print("\nClearing Django cache...")
    r.flushdb()
    print("✓ All cache cleared")
    
except Exception as e:
    print(f"Error connecting to Redis: {e}")
    print("\nTrying Docker Redis...")
    
    # Try connecting through Docker
    import subprocess
    try:
        result = subprocess.run(
            ['docker', 'exec', 'vfservices-redis-1', 'redis-cli', 'FLUSHDB'],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✓ Cache cleared via Docker")
        else:
            print(f"Failed to clear cache: {result.stderr}")
    except Exception as docker_error:
        print(f"Docker method also failed: {docker_error}")