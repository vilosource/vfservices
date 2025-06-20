"""
Custom exceptions for Identity Admin app
"""


class IdentityAdminError(Exception):
    """Base exception for Identity Admin app"""
    pass


class APIError(IdentityAdminError):
    """Base exception for API-related errors"""
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(APIError):
    """JWT token invalid or expired"""
    pass


class PermissionError(APIError):
    """User lacks required permissions"""
    pass


class ValidationError(APIError):
    """Invalid data provided"""
    pass


class NotFoundError(APIError):
    """Resource not found"""
    pass


class NetworkError(APIError):
    """Network connectivity issues"""
    pass


class TimeoutError(APIError):
    """API request timed out"""
    pass