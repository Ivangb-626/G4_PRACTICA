"""
LLM Response Caching with TTL
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CacheEntry:
    """Single cache entry with TTL."""
    
    def __init__(self, value: str, ttl_seconds: int = 3600):
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > self.ttl_seconds
    
    def __repr__(self) -> str:
        age = (datetime.now() - self.created_at).total_seconds()
        return f"CacheEntry(age={age:.1f}s, ttl={self.ttl_seconds}s)"


class LLMCache:
    """
    In-memory cache for LLM responses.
    Caches prompts to avoid redundant API calls.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    @staticmethod
    def _hash_prompt(system_prompt: str, user_prompt: str) -> str:
        """Generate hash key for prompt pair."""
        combined = f"{system_prompt}|{user_prompt}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Get cached response if available and not expired.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            Cached response or None
        """
        key = self._hash_prompt(system_prompt, user_prompt)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        entry = self.cache[key]
        
        if entry.is_expired():
            del self.cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry.value
    
    def set(self, system_prompt: str, user_prompt: str, response: str, ttl: Optional[int] = None) -> None:
        """
        Store response in cache.
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            response: LLM response
            ttl: Time to live in seconds (uses default if None)
        """
        key = self._hash_prompt(system_prompt, user_prompt)
        ttl = ttl or self.default_ttl
        
        # Simple LRU: if full, remove oldest
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].created_at)
            del self.cache[oldest_key]
        
        self.cache[key] = CacheEntry(response, ttl)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for k in expired_keys:
            del self.cache[k]
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'entries': {
                k: f"{v}" for k, v in list(self.cache.items())[:5]  # Show first 5
            }
        }


# Global cache instance
_llm_cache = LLMCache()


def get_llm_cache() -> LLMCache:
    """Get global LLM cache instance."""
    return _llm_cache
