"""
Centralized error definitions and handlers for the API
"""
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base class for API errors with status code and message."""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class ValidationError(APIError):
    """Input validation errors (400)"""
    def __init__(self, message: str):
        super().__init__(message, 400, "VALIDATION_ERROR")


class AuthenticationError(APIError):
    """Authentication failures (401)"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, 401, "AUTH_ERROR")


class AuthorizationError(APIError):
    """Authorization failures (403)"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403, "AUTHZ_ERROR")


class NotFoundError(APIError):
    """Resource not found (404)"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", 404, "NOT_FOUND")


class ConflictError(APIError):
    """Resource conflict (409)"""
    def __init__(self, message: str):
        super().__init__(message, 409, "CONFLICT_ERROR")


class GameError(APIError):
    """Game logic errors (400/409)"""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code, "GAME_ERROR")


class AIServiceError(APIError):
    """AI service errors (503)"""
    def __init__(self, message: str = "AI service unavailable"):
        super().__init__(message, 503, "AI_SERVICE_ERROR")


def format_error_response(error: Exception) -> Tuple[Dict[str, Any], int]:
    """
    Format error response with consistent structure.
    
    Args:
        error: Exception to format
        
    Returns:
        Tuple of (response dict, status code)
    """
    if isinstance(error, APIError):
        return {
            'success': False,
            'error': error.error_code,
            'message': error.message
        }, error.status_code
    
    # Unexpected error - don't expose internals
    logger.exception("Unexpected error", exc_info=error)
    return {
        'success': False,
        'error': 'INTERNAL_SERVER_ERROR',
        'message': 'An unexpected error occurred'
    }, 500


def format_success_response(data: Any = None, message: str = None) -> Dict[str, Any]:
    """
    Format successful response with consistent structure.
    
    Args:
        data: Response payload
        message: Optional success message
        
    Returns:
        Response dict
    """
    response = {'success': True}
    if message:
        response['message'] = message
    if data is not None:
        response['data'] = data
    return response
