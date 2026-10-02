"""
MuleGuard IP-Level Rate Limiter
Thread-safe, sliding-window in-memory rate limiter for authentication endpoints.
Configured via environment variables with Retry-After header and audit integration.
"""

import os
import time
import threading
from fastapi import Request, HTTPException, status

# Configurable limits via environment variables
DEFAULT_MAX_REQUESTS = 30
DEFAULT_WINDOW_SECONDS = 60


def get_rate_limit_config(ip: str | None = None) -> tuple[int, int]:
    """Reads rate limit configuration from environment variables with local loopback grace."""
    try:
        max_requests = int(os.getenv("AUTH_RATE_LIMIT_MAX_REQUESTS", str(DEFAULT_MAX_REQUESTS)))
    except ValueError:
        max_requests = DEFAULT_MAX_REQUESTS

    try:
        window_seconds = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", str(DEFAULT_WINDOW_SECONDS)))
    except ValueError:
        window_seconds = DEFAULT_WINDOW_SECONDS

    # Provide higher threshold for localhost/developer testing
    if ip in ("127.0.0.1", "::1", "localhost"):
        max_requests = max(max_requests, 60)

    return max(1, max_requests), max(1, window_seconds)


class SlidingWindowRateLimiter:
    """Thread-safe sliding window rate limiter tracking request timestamps per IP."""

    def __init__(self):
        self._lock = threading.Lock()
        self._records: dict[str, list[float]] = {}
        self._last_cleanup = time.time()

    def is_allowed(self, ip: str) -> tuple[bool, int]:
        """
        Checks if a request from the given IP is allowed under the configured window.
        Returns: (allowed: bool, retry_after_seconds: int)
        """
        max_requests, window_seconds = get_rate_limit_config(ip)
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            # Periodic cleanup of stale IPs every 5 minutes or 1000 items to avoid memory leaks
            if now - self._last_cleanup > 300 or len(self._records) > 1000:
                self._cleanup_stale(cutoff)

            timestamps = self._records.get(ip, [])
            # Evict timestamps outside the sliding window
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                # Calculate remaining seconds until the oldest request leaves the window
                oldest_timestamp = valid_timestamps[0]
                retry_after = max(1, int(oldest_timestamp + window_seconds - now) + 1)
                self._records[ip] = valid_timestamps
                return False, retry_after

            valid_timestamps.append(now)
            self._records[ip] = valid_timestamps
            return True, 0

    def _cleanup_stale(self, cutoff: float):
        """Purges IPs that have had no activity within the window."""
        stale_ips = [ip for ip, times in self._records.items() if not times or times[-1] <= cutoff]
        for ip in stale_ips:
            self._records.pop(ip, None)
        self._last_cleanup = time.time()

    def reset_for_ip(self, ip: str):
        """Resets the rate limit tracking for a specific IP (useful in testing)."""
        with self._lock:
            self._records.pop(ip, None)

    def clear(self):
        """Clears all tracked records."""
        with self._lock:
            self._records.clear()


# Global in-memory rate limiter instance
auth_rate_limiter = SlidingWindowRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extracts client IP, respecting X-Forwarded-For if behind a proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in X-Forwarded-For is the original client
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


def check_auth_rate_limit(request: Request):
    """
    FastAPI dependency that enforces IP rate limiting on sensitive auth endpoints.
    Raises HTTP 429 Too Many Requests with Retry-After header if limit exceeded.
    """
    client_ip = get_client_ip(request)
    allowed, retry_after = auth_rate_limiter.is_allowed(client_ip)

    if not allowed:
        # Import log_audit lazily to avoid circular imports
        from app.services.auth_service import log_audit
        ua = request.headers.get("user-agent", "")
        log_audit(
            event_type="RATE_LIMIT_EXCEEDED",
            user_id=None,
            employee_id=None,
            ip_address=client_ip,
            user_agent=ua,
            outcome="BLOCKED",
            failure_reason="IP_RATE_LIMIT_EXCEEDED",
            details={"retry_after": retry_after}
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many authentication attempts from this IP. Please try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
