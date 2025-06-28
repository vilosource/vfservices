"""
Rate limiting module for Azure RM Proxy.
Implements per-user and per-IP rate limiting.
"""
from fastapi import Request, HTTPException, status
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
import logging
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter implementation with sliding window.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_minute_authenticated: int = 120,
        cleanup_interval: int = 60
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_minute_authenticated = requests_per_minute_authenticated
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = cleanup_interval
        self._cleanup_task = None
        
    async def start(self):
        """Start the cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Rate limiter cleanup task started")
    
    async def stop(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Rate limiter cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Periodically clean up old request records."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_old_requests()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup: {str(e)}")
    
    def _cleanup_old_requests(self):
        """Remove request records older than 1 minute."""
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        keys_to_delete = []
        for key, timestamps in self.requests.items():
            # Keep only recent timestamps
            self.requests[key] = [ts for ts in timestamps if ts > cutoff]
            
            # Mark empty keys for deletion
            if not self.requests[key]:
                keys_to_delete.append(key)
        
        # Delete empty keys
        for key in keys_to_delete:
            del self.requests[key]
        
        if keys_to_delete:
            logger.debug(f"Cleaned up {len(keys_to_delete)} rate limit keys")
    
    async def check_rate_limit(self, request: Request, user: Optional[Dict] = None):
        """
        Check if request should be rate limited.
        
        Args:
            request: FastAPI request object
            user: Optional authenticated user dictionary
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Determine rate limit key and limit
        if user:
            # Use user ID for authenticated users
            key = f"user:{user.get('user_id', 'unknown')}"
            limit = self.requests_per_minute_authenticated
            
            # Admin users get higher limits
            if 'azure:admin' in user.get('roles', []):
                limit = limit * 2
        else:
            # Use IP address for anonymous users
            client_host = request.client.host if request.client else "unknown"
            key = f"ip:{client_host}"
            limit = self.requests_per_minute
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests for this key
        self.requests[key] = [ts for ts in self.requests[key] if ts > minute_ago]
        
        # Check limit
        if len(self.requests[key]) >= limit:
            # Calculate when they can try again
            oldest_request = min(self.requests[key])
            retry_after = int((oldest_request + timedelta(minutes=1) - now).total_seconds())
            
            logger.warning(f"Rate limit exceeded for {key}: {len(self.requests[key])}/{limit}")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Record this request
        self.requests[key].append(now)
    
    def get_remaining_requests(self, request: Request, user: Optional[Dict] = None) -> Dict[str, int]:
        """
        Get remaining requests for current time window.
        
        Returns:
            Dictionary with limit, remaining, and reset_time
        """
        # Determine rate limit key and limit
        if user:
            key = f"user:{user.get('user_id', 'unknown')}"
            limit = self.requests_per_minute_authenticated
            if 'azure:admin' in user.get('roles', []):
                limit = limit * 2
        else:
            client_host = request.client.host if request.client else "unknown"
            key = f"ip:{client_host}"
            limit = self.requests_per_minute
        
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Count recent requests
        recent_requests = [ts for ts in self.requests.get(key, []) if ts > minute_ago]
        remaining = max(0, limit - len(recent_requests))
        
        # Calculate reset time (when oldest request expires)
        if recent_requests:
            oldest = min(recent_requests)
            reset_time = int((oldest + timedelta(minutes=1)).timestamp())
        else:
            reset_time = int((now + timedelta(minutes=1)).timestamp())
        
        return {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time
        }


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=int(os.getenv('RATE_LIMIT_ANONYMOUS', '60')),
    requests_per_minute_authenticated=int(os.getenv('RATE_LIMIT_AUTHENTICATED', '120'))
)


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to apply rate limiting to all requests.
    
    This should be added to the FastAPI app.
    """
    # Skip rate limiting for health checks and docs
    if request.url.path in ['/api/ping', '/docs', '/redoc', '/openapi.json']:
        return await call_next(request)
    
    # Get user from request state (set by auth middleware)
    user = getattr(request.state, 'user', None)
    
    try:
        # Check rate limit
        await rate_limiter.check_rate_limit(request, user)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        rate_info = rate_limiter.get_remaining_requests(request, user)
        response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
        response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
        response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
        
        return response
        
    except HTTPException:
        # Re-raise rate limit exceptions
        raise
    except Exception as e:
        # Log other errors but don't block request
        logger.error(f"Error in rate limit middleware: {str(e)}")
        return await call_next(request)