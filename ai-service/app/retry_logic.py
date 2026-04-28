"""
Advanced retry logic with exponential backoff and circuit breaker
"""
import asyncio
import logging
from typing import Callable, Any, Optional, Type
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitBreakerState:
    """States for circuit breaker pattern."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service is failing, requests rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Name of breaker (for logging)
            failure_threshold: Failures before opening
            recovery_timeout: Seconds before trying recovery (HALF_OPEN)
            success_threshold: Successes in HALF_OPEN before closing
        """
        self.name = name
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.last_failure_time: Optional[datetime] = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args, **kwargs: Function arguments
            
        Returns:
            Function result
            
        Raises:
            RuntimeError: If circuit is OPEN
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
            else:
                raise RuntimeError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Async version of call()."""
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_recovery():
                self.state = CircuitBreakerState.HALF_OPEN
                self.success_count = 0
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
            else:
                raise RuntimeError(f"Circuit breaker {self.name} is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if not self.last_failure_time:
            return True
        
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitBreakerState.CLOSED
                self.failure_count = 0
                logger.info(f"[{self.name}] Circuit breaker closed - service recovered")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"[{self.name}] Circuit breaker reopened - service still failing")
        elif self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitBreakerState.OPEN
                logger.error(f"[{self.name}] Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> str:
        """Get current state."""
        return self.state


async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,)
) -> Any:
    """
    Call function with exponential backoff retry logic.
    
    Args:
        func: Async function to call
        max_attempts: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Multiply delay by this each retry
        retryable_exceptions: Exception types to retry on
        
    Returns:
        Function result
        
    Raises:
        Last exception if all retries exhausted
    """
    last_exception = None
    delay = base_delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except retryable_exceptions as e:
            last_exception = e
            
            if attempt >= max_attempts:
                logger.error(f"Max retries ({max_attempts}) exhausted")
                raise
            
            logger.warning(f"Attempt {attempt} failed, retrying in {delay:.1f}s: {e}")
            await asyncio.sleep(delay)
            
            delay = min(delay * exponential_base, max_delay)
    
    raise last_exception


def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    retryable_exceptions: tuple = (Exception,)
):
    """
    Decorator for synchronous functions with retry logic.
    
    Usage:
        @retry_sync(max_attempts=3)
        def call_api():
            return requests.get(url)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            delay = base_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_attempts:
                        logger.error(f"Max retries ({max_attempts}) exhausted")
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed, retrying in {delay:.1f}s: {e}")
                    asyncio.sleep(delay)
                    
                    delay = min(delay * exponential_base, max_delay)
            
            raise last_exception
        
        return wrapper
    
    return decorator
