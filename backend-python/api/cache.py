"""
High-performance caching layer for <0.2s response times.
Uses in-memory cache with TTL, can be upgraded to Redis for distributed systems.
"""

import time
import hashlib
import json
import logging
from typing import Any, Optional, Callable, Dict, Union
from functools import wraps
from collections import OrderedDict
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security check fails."""

    pass


# Forward declaration for type hint
class CacheEntry:
    """Cache entry with TTL."""

    def __init__(self, value: Any, ttl: float = 300.0):
        self.value = value
        self.expires_at = time.time() + ttl
        self.created_at = time.time()

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


# In-memory cache with LRU eviction
_cache: OrderedDict[str, Union[Dict[str, Any], CacheEntry]] = OrderedDict()
_cache_max_size = 10000
_cache_stats = {"hits": 0, "misses": 0, "evictions": 0}


def _make_key(*args, **kwargs) -> str:
    """Create cache key from function arguments."""
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_str.encode()).hexdigest()


def _evict_expired():
    """Remove expired entries."""
    expired_keys = [k for k, v in _cache.items() if isinstance(v, CacheEntry) and v.is_expired()]
    for key in expired_keys:
        _cache.pop(key, None)
        _cache_stats["evictions"] += 1


def _evict_lru():
    """Evict least recently used entry if cache is full."""
    if len(_cache) >= _cache_max_size:
        _cache.popitem(last=False)  # Remove oldest
        _cache_stats["evictions"] += 1


def get(key: str) -> Optional[Any]:
    """Get value from cache."""
    _evict_expired()

    entry = _cache.get(key)
    if entry is None:
        _cache_stats["misses"] += 1
        # Record Prometheus metric
        try:
            from api.prometheus import metrics

            metrics.record_cache_miss("lru_cache")
        except Exception:
            pass
        return None

    if isinstance(entry, CacheEntry) and entry.is_expired():
        _cache.pop(key, None)
        _cache_stats["misses"] += 1
        try:
            from api.prometheus import metrics

            metrics.record_cache_miss("lru_cache")
        except Exception:
            pass
        return None

    # Move to end (most recently used)
    _cache.move_to_end(key)
    _cache_stats["hits"] += 1
    # Record Prometheus metric
    try:
        from api.prometheus import metrics

        metrics.record_cache_hit("lru_cache")
    except Exception:
        pass
    return entry.value if isinstance(entry, CacheEntry) else entry


def set(key: str, value: Any, ttl: float = 300.0):
    """Set value in cache with TTL."""
    _evict_expired()
    _evict_lru()

    _cache[key] = CacheEntry(value, ttl)
    _cache.move_to_end(key)

    # Update Prometheus metric
    try:
        from api.prometheus import metrics

        metrics.update_cache_size(len(_cache))
    except Exception:
        pass


def delete(key: str):
    """Delete key from cache."""
    _cache.pop(key, None)


def clear():
    """Clear all cache entries."""
    _cache.clear()
    _cache_stats["hits"] = 0
    _cache_stats["misses"] = 0
    _cache_stats["evictions"] = 0


def get_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    _evict_expired()
    hit_rate = (
        _cache_stats["hits"] / (_cache_stats["hits"] + _cache_stats["misses"])
        if (_cache_stats["hits"] + _cache_stats["misses"]) > 0
        else 0
    )

    return {
        "size": len(_cache),
        "max_size": _cache_max_size,
        "hits": _cache_stats["hits"],
        "misses": _cache_stats["misses"],
        "evictions": _cache_stats["evictions"],
        "hit_rate": hit_rate,
    }


def cached(ttl: float = 300.0, key_prefix: str = ""):
    """Decorator to cache function results."""

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{_make_key(*args, **kwargs)}"
            cached_value = get(cache_key)

            if cached_value is not None:
                return cached_value

            result = await func(*args, **kwargs)
            set(cache_key, result, ttl)
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{_make_key(*args, **kwargs)}"
            cached_value = get(cache_key)

            if cached_value is not None:
                return cached_value

            result = func(*args, **kwargs)
            set(cache_key, result, ttl)
            return result

        return (
            async_wrapper
            if hasattr(func, "__code__") and "async" in str(func.__code__.co_flags)
            else sync_wrapper
        )

    return decorator


# Pre-warmed caches for critical data
_verification_keys_cache: Dict[str, Any] = {}


def cache_verification_key(circuit: str, vk: Dict[str, Any]):
    """Cache verification key (long TTL, rarely changes)."""
    _verification_keys_cache[circuit] = vk


def get_verification_key(circuit: str) -> Optional[Dict[str, Any]]:
    """Get cached verification key."""
    return _verification_keys_cache.get(circuit)


def load_vkey_from_disk(circuit: str) -> Optional[Dict[str, Any]]:
    """Load verification key from disk and cache it. Verifies integrity."""
    cached = get_verification_key(circuit)
    if cached:
        return cached

    vkey_path = (
        Path(__file__).parent.parent / "zkp" / "artifacts" / circuit / "verification_key.json"
    )
    hash_path = (
        Path(__file__).parent.parent / "zkp" / "artifacts" / circuit / "verification_key.sha256"
    )

    if not vkey_path.exists():
        return None

    try:
        with open(vkey_path, "r") as f:
            vkey_data = json.load(f)

        # Verify integrity if hash file exists
        if hash_path.exists():
            vkey_str = json.dumps(vkey_data, sort_keys=True)
            computed_hash = hashlib.sha256(vkey_str.encode()).hexdigest()

            with open(hash_path, "r") as f:
                expected_hash = f.read().strip()

            if computed_hash != expected_hash:
                logger.error(f"Verification key integrity check FAILED for {circuit}")
                logger.error(f"Expected: {expected_hash}, Computed: {computed_hash}")
                raise SecurityError(f"Verification key integrity check failed for {circuit}")

            logger.debug(f"Verification key integrity verified for {circuit}")

        cache_verification_key(circuit, vkey_data)
        return vkey_data
    except Exception as e:
        logger.error(f"Failed to load vkey for {circuit}: {e}")
        return None
