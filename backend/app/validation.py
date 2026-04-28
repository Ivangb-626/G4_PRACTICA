"""
Input validation utilities
"""
import re
from typing import Any, List
from .errors import ValidationError


# Validation patterns
USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_-]{3,30}$')
EMAIL_PATTERN = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
GAME_NAME_PATTERN = re.compile(r'^[A-Za-z0-9_\- ]{1,100}$')

# Constants
VALID_GALAXY_SIZES = ['small', 'medium', 'large']
VALID_DIFFICULTIES = ['easy', 'normal', 'hard']
VALID_GOVERNMENTS = ['dictatorship', 'democracy', 'unification', 'feudalism']
MAX_STRING_LENGTH = 500


def validate_username(username: str) -> str:
    """Validate username format and length."""
    if not username or not isinstance(username, str):
        raise ValidationError("Username must be a non-empty string")
    
    username = username.strip()
    if not USERNAME_PATTERN.match(username):
        raise ValidationError("Username must be 3-30 characters, alphanumeric with hyphens and underscores only")
    
    return username


def validate_email(email: str) -> str:
    """Validate email format."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string")
    
    email = email.strip().lower()
    if not EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email format")
    
    if len(email) > 254:  # RFC 5321
        raise ValidationError("Email too long")
    
    return email


def validate_password(password: str) -> str:
    """Validate password strength."""
    if not password or not isinstance(password, str):
        raise ValidationError("Password must be a non-empty string")
    
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")
    
    if len(password) > 128:
        raise ValidationError("Password too long")
    
    return password


def validate_game_name(name: str) -> str:
    """Validate game name."""
    if not name or not isinstance(name, str):
        raise ValidationError("Game name must be a non-empty string")
    
    name = name.strip()
    if len(name) < 1 or len(name) > 100:
        raise ValidationError("Game name must be 1-100 characters")
    
    if not GAME_NAME_PATTERN.match(name):
        raise ValidationError("Game name contains invalid characters")
    
    return name


def validate_galaxy_size(size: str) -> str:
    """Validate galaxy size is one of allowed values."""
    if size not in VALID_GALAXY_SIZES:
        raise ValidationError(f"Galaxy size must be one of: {', '.join(VALID_GALAXY_SIZES)}")
    return size


def validate_difficulty(difficulty: str) -> str:
    """Validate difficulty level."""
    if difficulty not in VALID_DIFFICULTIES:
        raise ValidationError(f"Difficulty must be one of: {', '.join(VALID_DIFFICULTIES)}")
    return difficulty


def validate_number_range(value: Any, min_val: int, max_val: int, name: str) -> int:
    """Validate number is within range."""
    try:
        num = int(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{name} must be an integer")
    
    if num < min_val or num > max_val:
        raise ValidationError(f"{name} must be between {min_val} and {max_val}")
    
    return num


def validate_required_fields(data: dict, fields: List[str]) -> None:
    """Validate that required fields are present and non-empty."""
    if not data:
        raise ValidationError("Request body is empty")
    
    missing = []
    for field in fields:
        if field not in data or data[field] is None or data[field] == '':
            missing.append(field)
    
    if missing:
        raise ValidationError(f"Missing required fields: {', '.join(missing)}")


def sanitize_string(value: str, max_length: int = MAX_STRING_LENGTH) -> str:
    """Sanitize string input: strip whitespace, limit length."""
    if not isinstance(value, str):
        raise ValidationError("Value must be a string")
    
    value = value.strip()
    
    if len(value) > max_length:
        raise ValidationError(f"Value too long (max {max_length} characters)")
    
    return value


def validate_enum(value: str, allowed: List[str], field_name: str) -> str:
    """Validate value is one of allowed enum values."""
    if value not in allowed:
        raise ValidationError(f"{field_name} must be one of: {', '.join(allowed)}")
    return value
