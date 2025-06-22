"""
Menu service for aggregating menus from multiple microservices.
"""
import logging
import requests
from django.conf import settings
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

logger = logging.getLogger(__name__)


class MenuService:
    """Service for fetching and aggregating menus from multiple services."""
    
    def __init__(self):
        self.cache_ttl = getattr(settings, 'MENU_CACHE_TTL', 300)  # 5 minutes default
        self.api_timeout = getattr(settings, 'MENU_API_TIMEOUT', 2)  # 2 seconds default
        self.service_urls = {
            'inventory': settings.INVENTORY_API_URL,
            'billing': settings.BILLING_API_URL,
        }
    
    def get_menu(self, menu_name, user_token):
        """
        Get aggregated menu from all services.
        
        Args:
            menu_name: Name of the menu to fetch
            user_token: JWT token for authentication
            
        Returns:
            dict: Aggregated menu data
        """
        # Create cache key including user to ensure permissions are respected
        cache_key = f"menu:{menu_name}:{user_token[:20]}"  # Use first 20 chars of token
        
        # Check cache first
        cached_menu = cache.get(cache_key)
        if cached_menu:
            logger.debug(f"Menu '{menu_name}' retrieved from cache")
            return cached_menu
        
        # Fetch from services
        aggregated_menu = self._fetch_and_aggregate_menu(menu_name, user_token)
        
        # Cache the result
        if aggregated_menu['items']:
            cache.set(cache_key, aggregated_menu, self.cache_ttl)
            logger.debug(f"Menu '{menu_name}' cached for {self.cache_ttl} seconds")
        
        return aggregated_menu
    
    def _fetch_and_aggregate_menu(self, menu_name, user_token):
        """
        Fetch menu from all services and aggregate results.
        
        Args:
            menu_name: Name of the menu to fetch
            user_token: JWT token for authentication
            
        Returns:
            dict: Aggregated menu data
        """
        all_items = []
        service_responses = {}
        
        # Use ThreadPoolExecutor for parallel requests
        with ThreadPoolExecutor(max_workers=len(self.service_urls)) as executor:
            # Submit all requests
            future_to_service = {
                executor.submit(
                    self._fetch_menu_from_service,
                    service_name,
                    service_url,
                    menu_name,
                    user_token
                ): service_name
                for service_name, service_url in self.service_urls.items()
            }
            
            # Collect results
            for future in as_completed(future_to_service):
                service_name = future_to_service[future]
                try:
                    result = future.result()
                    if result:
                        service_responses[service_name] = result
                        all_items.extend(result.get('items', []))
                except Exception as e:
                    logger.error(f"Error fetching menu from {service_name}: {str(e)}")
        
        # Sort items by order
        all_items.sort(key=lambda x: x.get('order', 999))
        
        return {
            'menu_name': menu_name,
            'items': all_items,
            'sources': list(service_responses.keys()),
            'version': '1.0'
        }
    
    def _fetch_menu_from_service(self, service_name, service_url, menu_name, user_token):
        """
        Fetch menu from a single service.
        
        Args:
            service_name: Name of the service
            service_url: Base URL of the service
            menu_name: Name of the menu to fetch
            user_token: JWT token for authentication
            
        Returns:
            dict: Menu data from service or None if error
        """
        try:
            # Construct URL
            url = f"{service_url}/api/menus/{menu_name}/"
            
            # Make request
            headers = {
                'Authorization': f'Bearer {user_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.api_timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully fetched menu from {service_name}")
                return response.json()
            elif response.status_code == 404:
                logger.debug(f"Menu '{menu_name}' not found in {service_name}")
                return None
            else:
                logger.warning(
                    f"Error fetching menu from {service_name}: "
                    f"Status {response.status_code}"
                )
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching menu from {service_name}")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning(f"Connection error fetching menu from {service_name}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching menu from {service_name}: {str(e)}")
            return None
    
    def clear_cache(self, menu_name=None, user_token=None):
        """
        Clear menu cache.
        
        Args:
            menu_name: Specific menu to clear (optional)
            user_token: Specific user's cache to clear (optional)
        """
        if menu_name and user_token:
            cache_key = f"menu:{menu_name}:{user_token[:20]}"
            cache.delete(cache_key)
            logger.info(f"Cleared cache for menu '{menu_name}'")
        else:
            # Clear all menu caches (pattern-based clearing if supported)
            logger.info("Clearing all menu caches")
            # Note: This requires cache backend that supports pattern deletion
            # For now, we'll just log it
            pass