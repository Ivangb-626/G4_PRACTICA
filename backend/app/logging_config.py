"""
Structured logging configuration for the application
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(app_name: str = 'masterofhostias', log_dir: str = 'logs') -> logging.Logger:
    """
    Configure structured logging with both file and console output.
    
    Args:
        app_name: Name for the logger
        log_dir: Directory to store log files
        
    Returns:
        Configured logger instance
    """
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Log format: timestamp | level | module | message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        f'{log_dir}/app.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        f'{log_dir}/error.log',
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    # Console handler (INFO level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Silence PyMongo/Motor verbose logging
    logging.getLogger('pymongo').setLevel(logging.WARNING)
    logging.getLogger('pymongo.command').setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.
    
    Args:
        name: Logger name (usually __name__ from module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger('masterofhostias.' + name)


class RequestLogger:
    """Middleware for logging HTTP requests and responses."""
    
    @staticmethod
    def log_request(method: str, path: str, user_id: str = None) -> None:
        """Log incoming request."""
        logger = get_logger('request')
        user_info = f"(user: {user_id})" if user_id else ""
        logger.info(f"→ {method} {path} {user_info}")
    
    @staticmethod
    def log_response(method: str, path: str, status_code: int, duration_ms: float) -> None:
        """Log outgoing response."""
        logger = get_logger('request')
        level = logging.WARNING if status_code >= 400 else logging.INFO
        logger.log(level, f"← {method} {path} {status_code} ({duration_ms:.1f}ms)")
    
    @staticmethod
    def log_error(error: str, context: dict = None) -> None:
        """Log error with context."""
        logger = get_logger('error')
        context_str = f" | {context}" if context else ""
        logger.error(f"{error}{context_str}")
