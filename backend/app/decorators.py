"""
Decorators for Flask routes
"""
from functools import wraps
from typing import Callable, Any
from flask import jsonify, request, g
from .errors import APIError, format_error_response, format_success_response, AuthenticationError
from .logging_config import get_logger
from .auth.jwt_handler import verify_token

logger = get_logger('decorators')


def handle_errors(f: Callable) -> Callable:
    """
    Decorator to handle errors in route handlers.
    Wraps exceptions in appropriate HTTP responses.
    
    Usage:
        @app.route('/api/endpoint')
        @handle_errors
        def my_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> tuple:
        try:
            result = f(*args, **kwargs)
            return result
        except APIError as e:
            logger.warning(f"API Error in {f.__name__}: {e.message}")
            response, status = format_error_response(e)
            return jsonify(response), status
        except Exception as e:
            logger.exception(f"Unexpected error in {f.__name__}")
            response, status = format_error_response(e)
            return jsonify(response), status
    
    return decorated_function


def require_json(f: Callable) -> Callable:
    """
    Decorator to ensure request has JSON body.
    
    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @require_json
        def my_endpoint():
            data = request.get_json()  # guaranteed not None
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> tuple:
        if not request.is_json:
            response, status = format_error_response(
                APIError("Content-Type must be application/json", 400)
            )
            return jsonify(response), status
        
        data = request.get_json()
        if data is None:
            response, status = format_error_response(
                APIError("Request body is empty", 400)
            )
            return jsonify(response), status
        
        return f(*args, **kwargs)
    
    return decorated_function


def token_required_new(f: Callable) -> Callable:
    """
    Decorator to verify JWT token in Authorization header.
    Sets g.user_id if valid.
    
    Usage:
        @app.route('/api/protected')
        @token_required_new
        def my_endpoint():
            user_id = g.user_id  # Set by decorator
    """
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> tuple:
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            response, status = format_error_response(AuthenticationError("Missing token"))
            return jsonify(response), status
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            user_id = verify_token(token)
            if not user_id:
                raise AuthenticationError("Invalid token")
            g.user_id = user_id
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            response, status = format_error_response(AuthenticationError("Invalid token"))
            return jsonify(response), status
        
        return f(*args, **kwargs)
    
    return decorated_function
