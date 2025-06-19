"""
Redis client for attribute caching and pub/sub
"""

import redis
import json
import logging
from typing import Optional, Dict, List, Any
from django.conf import settings
from .models import UserAttributes

logger = logging.getLogger(__name__)


class RedisAttributeClient:
    """
    Client for managing user attributes in Redis.
    
    This class handles:
    - Storing/retrieving user attributes
    - Cache invalidation via pub/sub
    - TTL management
    """
    
    def __init__(self, host: str = None, port: int = None, db: int = 0, 
                 decode_responses: bool = False, ttl: int = None):
        """
        Initialize Redis client.
        
        Args:
            host: Redis host (defaults to settings.REDIS_HOST)
            port: Redis port (defaults to settings.REDIS_PORT)
            db: Redis database number
            decode_responses: Whether to decode responses to strings
            ttl: Default TTL for cached attributes in seconds (defaults to settings.RBAC_ABAC_CACHE_TTL or 86400)
        """
        self.host = host or getattr(settings, 'REDIS_HOST', 'localhost')
        self.port = port or getattr(settings, 'REDIS_PORT', 6379)
        self.db = db
        # Default to 24 hours (86400 seconds) if not specified
        self.ttl = ttl or getattr(settings, 'RBAC_ABAC_CACHE_TTL', 86400)
        
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=decode_responses
        )
        
        # Test connection
        try:
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def get_user_key(self, user_id: int, service_name: str) -> str:
        """Generate Redis key for user attributes."""
        return f"user:{user_id}:attrs:{service_name}"
    
    def get_user_attributes(self, user_id: int, service_name: str) -> Optional[UserAttributes]:
        """
        Retrieve user attributes from Redis.
        
        Args:
            user_id: User ID
            service_name: Name of the service requesting attributes
            
        Returns:
            UserAttributes object or None if not found
        """
        key = self.get_user_key(user_id, service_name)
        
        try:
            data = self.client.hgetall(key)
            if not data:
                logger.debug(f"No attributes found for user {user_id} in service {service_name}")
                return None
            
            return UserAttributes.from_redis_data(data)
        except Exception as e:
            logger.error(f"Error retrieving attributes for user {user_id}: {e}")
            return None
    
    def set_user_attributes(self, user_id: int, service_name: str, 
                          attributes: UserAttributes, ttl: int = None) -> bool:
        """
        Store user attributes in Redis.
        
        Args:
            user_id: User ID
            service_name: Name of the service
            attributes: UserAttributes object
            ttl: TTL in seconds (uses default if not specified)
            
        Returns:
            True if successful
        """
        key = self.get_user_key(user_id, service_name)
        ttl = ttl or self.ttl
        
        try:
            # Store as hash
            data = attributes.to_redis_data()
            
            # Use pipeline for atomic operation
            pipe = self.client.pipeline()
            pipe.delete(key)  # Clear existing data
            pipe.hmset(key, data)
            pipe.expire(key, ttl)
            pipe.execute()
            
            logger.debug(f"Stored attributes for user {user_id} in service {service_name}")
            return True
        except Exception as e:
            logger.error(f"Error storing attributes for user {user_id}: {e}")
            return False
    
    def invalidate_user_attributes(self, user_id: int, service_name: str = None) -> int:
        """
        Invalidate cached attributes for a user.
        
        Args:
            user_id: User ID
            service_name: Specific service or None for all services
            
        Returns:
            Number of keys deleted
        """
        if service_name:
            keys = [self.get_user_key(user_id, service_name)]
        else:
            # Delete all service attributes for this user
            pattern = f"user:{user_id}:attrs:*"
            keys = list(self.client.scan_iter(match=pattern))
        
        if keys:
            return self.client.delete(*keys)
        return 0
    
    def publish_invalidation(self, user_id: int, service_name: str = None):
        """
        Publish cache invalidation message via pub/sub.
        
        Args:
            user_id: User ID
            service_name: Specific service or None for all
        """
        channel = "rbac_abac:invalidations"
        message = {
            'user_id': user_id,
            'service_name': service_name,
            'action': 'invalidate'
        }
        
        try:
            self.client.publish(channel, json.dumps(message))
            logger.debug(f"Published invalidation for user {user_id}")
        except Exception as e:
            logger.error(f"Error publishing invalidation: {e}")
    
    def subscribe_to_invalidations(self, callback):
        """
        Subscribe to cache invalidation messages.
        
        Args:
            callback: Function to call with (user_id, service_name)
        """
        pubsub = self.client.pubsub()
        pubsub.subscribe("rbac_abac:invalidations")
        
        logger.info("Subscribed to cache invalidation messages")
        
        for message in pubsub.listen():
            if message['type'] == 'message':
                try:
                    data = json.loads(message['data'])
                    callback(data['user_id'], data.get('service_name'))
                except Exception as e:
                    logger.error(f"Error processing invalidation message: {e}")
    
    def health_check(self) -> bool:
        """Check if Redis connection is healthy."""
        try:
            return self.client.ping()
        except Exception:
            return False


# Global client instance (lazy initialization)
_redis_client: Optional[RedisAttributeClient] = None


def get_redis_client() -> RedisAttributeClient:
    """Get or create the global Redis client instance."""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisAttributeClient()
    return _redis_client


def get_user_attributes(user_id: int, service_name: str, auto_refresh: bool = True) -> Optional[UserAttributes]:
    """
    Convenience function to get user attributes with automatic cache refresh.
    
    Args:
        user_id: User ID
        service_name: Name of the service
        auto_refresh: Whether to attempt automatic refresh if cache miss
        
    Returns:
        UserAttributes object or None
    """
    client = get_redis_client()
    
    # Try to get from cache first
    attrs = client.get_user_attributes(user_id, service_name)
    
    # If not found and auto_refresh is enabled, try to refresh from identity provider
    if attrs is None and auto_refresh:
        attrs = refresh_user_attributes_from_identity_provider(user_id, service_name)
    
    return attrs


def refresh_user_attributes_from_identity_provider(user_id: int, service_name: str) -> Optional[UserAttributes]:
    """
    Refresh user attributes from the identity provider.
    
    This function makes an API call to the identity provider to fetch fresh
    user attributes and stores them in Redis.
    
    Args:
        user_id: User ID
        service_name: Name of the service
        
    Returns:
        UserAttributes object or None
    """
    try:
        import requests
        from django.conf import settings
        
        # Get identity provider URL from settings
        identity_provider_url = getattr(settings, 'IDENTITY_PROVIDER_URL', 'http://identity-provider:8000')
        
        # Make API call to identity provider to refresh attributes
        response = requests.post(
            f"{identity_provider_url}/api/refresh-user-cache/",
            json={
                'user_id': user_id,
                'service_name': service_name
            },
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            logger.info(f"Successfully refreshed attributes for user {user_id} from identity provider")
            # Try to get the refreshed attributes
            client = get_redis_client()
            return client.get_user_attributes(user_id, service_name)
        else:
            logger.error(f"Failed to refresh attributes from identity provider: {response.status_code}")
            
    except requests.RequestException as e:
        logger.error(f"Error connecting to identity provider: {e}")
    except Exception as e:
        logger.error(f"Unexpected error refreshing attributes: {e}")
    
    return None