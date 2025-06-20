"""
Tests for Redis attribute client
"""

import pytest
import redis
from unittest.mock import Mock, patch, MagicMock
import json
from common.rbac_abac.redis_client import RedisAttributeClient, get_user_attributes
from common.rbac_abac.models import UserAttributes


class TestRedisAttributeClient:
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        with patch('common.rbac_abac.redis_client.redis.Redis') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.ping.return_value = True
            yield mock_instance
    
    @pytest.fixture
    def client(self, mock_redis):
        """Create a RedisAttributeClient with mocked Redis."""
        return RedisAttributeClient(host='localhost', port=6379)
    
    def test_initialization(self, mock_redis):
        """Test client initialization and connection."""
        client = RedisAttributeClient(host='testhost', port=1234, ttl=600)
        
        assert client.host == 'testhost'
        assert client.port == 1234
        assert client.ttl == 600
        mock_redis.ping.assert_called_once()
    
    def test_initialization_with_connection_error(self):
        """Test handling connection errors during initialization."""
        with patch('common.rbac_abac.redis_client.redis.Redis') as mock:
            mock_instance = MagicMock()
            mock.return_value = mock_instance
            mock_instance.ping.side_effect = redis.ConnectionError("Connection failed")
            
            with pytest.raises(redis.ConnectionError):
                RedisAttributeClient()
    
    def test_get_user_key(self, client):
        """Test Redis key generation."""
        key = client.get_user_key(123, 'billing_api')
        assert key == 'user:123:attrs:billing_api'
    
    def test_get_user_attributes_success(self, client, mock_redis):
        """Test retrieving user attributes from Redis."""
        # Mock Redis response
        mock_redis.hgetall.return_value = {
            b'user_id': b'123',
            b'username': b'testuser',
            b'email': b'test@example.com',
            b'roles': b'["admin", "user"]',
            b'department': b'IT',
            b'admin_group_ids': b'[1, 2]'
        }
        
        attrs = client.get_user_attributes(123, 'billing_api')
        
        assert attrs is not None
        assert attrs.user_id == 123
        assert attrs.username == 'testuser'
        assert attrs.roles == ['admin', 'user']
        assert attrs.department == 'IT'
        
        mock_redis.hgetall.assert_called_once_with('user:123:attrs:billing_api')
    
    def test_get_user_attributes_not_found(self, client, mock_redis):
        """Test when user attributes are not in Redis."""
        mock_redis.hgetall.return_value = {}
        
        attrs = client.get_user_attributes(999, 'billing_api')
        assert attrs is None
    
    def test_get_user_attributes_error(self, client, mock_redis):
        """Test error handling when retrieving attributes."""
        mock_redis.hgetall.side_effect = Exception("Redis error")
        
        attrs = client.get_user_attributes(123, 'billing_api')
        assert attrs is None
    
    def test_set_user_attributes(self, client, mock_redis):
        """Test storing user attributes in Redis."""
        attrs = UserAttributes(
            user_id=123,
            username='testuser',
            email='test@example.com',
            roles=['admin'],
            department='Sales'
        )
        
        # Mock pipeline
        mock_pipe = MagicMock()
        mock_redis.pipeline.return_value = mock_pipe
        mock_pipe.execute.return_value = [True, True, True]
        
        result = client.set_user_attributes(123, 'billing_api', attrs, ttl=600)
        
        assert result == True
        mock_redis.pipeline.assert_called_once()
        mock_pipe.delete.assert_called_once_with('user:123:attrs:billing_api')
        mock_pipe.hmset.assert_called_once()
        mock_pipe.expire.assert_called_once_with('user:123:attrs:billing_api', 600)
        mock_pipe.execute.assert_called_once()
    
    def test_set_user_attributes_error(self, client, mock_redis):
        """Test error handling when storing attributes."""
        attrs = UserAttributes(
            user_id=123,
            username='testuser',
            email='test@example.com'
        )
        
        mock_redis.pipeline.side_effect = Exception("Redis error")
        
        result = client.set_user_attributes(123, 'billing_api', attrs)
        assert result == False
    
    def test_invalidate_user_attributes_single_service(self, client, mock_redis):
        """Test invalidating attributes for a specific service."""
        mock_redis.delete.return_value = 1
        
        count = client.invalidate_user_attributes(123, 'billing_api')
        
        assert count == 1
        mock_redis.delete.assert_called_once_with('user:123:attrs:billing_api')
    
    def test_invalidate_user_attributes_all_services(self, client, mock_redis):
        """Test invalidating attributes for all services."""
        # Mock scan_iter to return multiple keys
        mock_redis.scan_iter.return_value = [
            'user:123:attrs:billing_api',
            'user:123:attrs:inventory_api',
            'user:123:attrs:website'
        ]
        mock_redis.delete.return_value = 3
        
        count = client.invalidate_user_attributes(123)
        
        assert count == 3
        mock_redis.scan_iter.assert_called_once_with(match='user:123:attrs:*')
        mock_redis.delete.assert_called_once()
    
    def test_publish_invalidation(self, client, mock_redis):
        """Test publishing cache invalidation message."""
        client.publish_invalidation(123, 'billing_api')
        
        expected_message = json.dumps({
            'user_id': 123,
            'service_name': 'billing_api',
            'action': 'invalidate'
        })
        
        mock_redis.publish.assert_called_once_with(
            'rbac_abac:invalidations',
            expected_message
        )
    
    def test_publish_invalidation_error(self, client, mock_redis):
        """Test error handling in publish invalidation."""
        mock_redis.publish.side_effect = Exception("Publish error")
        
        # Should not raise exception
        client.publish_invalidation(123)
    
    def test_health_check(self, client, mock_redis):
        """Test Redis health check."""
        mock_redis.ping.return_value = True
        assert client.health_check() == True
        
        mock_redis.ping.side_effect = Exception("Connection lost")
        assert client.health_check() == False
    
    def test_subscribe_to_invalidations(self, client, mock_redis):
        """Test subscribing to invalidation messages."""
        # Mock pubsub
        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub
        
        # Mock messages
        mock_pubsub.listen.return_value = [
            {'type': 'subscribe', 'data': 1},
            {
                'type': 'message',
                'data': json.dumps({
                    'user_id': 123,
                    'service_name': 'billing_api',
                    'action': 'invalidate'
                })
            },
            {'type': 'message', 'data': 'invalid json'},  # Test error handling
        ]
        
        # Track callback calls
        callback_calls = []
        def test_callback(user_id, service_name):
            callback_calls.append((user_id, service_name))
            if len(callback_calls) >= 1:  # Stop after first valid message
                mock_pubsub.listen.return_value = []
        
        client.subscribe_to_invalidations(test_callback)
        
        # Verify subscription
        mock_pubsub.subscribe.assert_called_once_with('rbac_abac:invalidations')
        
        # Verify callback was called correctly
        assert len(callback_calls) == 1
        assert callback_calls[0] == (123, 'billing_api')


class TestGlobalFunctions:
    
    @patch('common.rbac_abac.redis_client.RedisAttributeClient')
    def test_get_user_attributes_function(self, mock_client_class):
        """Test the global get_user_attributes function."""
        # Mock client instance
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock return value
        expected_attrs = UserAttributes(
            user_id=123,
            username='testuser',
            email='test@example.com'
        )
        mock_client.get_user_attributes.return_value = expected_attrs
        
        # Test function
        attrs = get_user_attributes(123, 'billing_api')
        
        assert attrs == expected_attrs
        mock_client.get_user_attributes.assert_called_once_with(123, 'billing_api')