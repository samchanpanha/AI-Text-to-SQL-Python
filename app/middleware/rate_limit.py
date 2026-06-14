"""
Per-user rate limiting middleware.

Uses an in-memory sliding window counter. For multi-worker deployments,
replace with Redis-backed rate limiter.
"""

import time
import logging
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.database.connection import SessionLocal
from app.database.models import User
from app.auth.jwt import decode_access_token
from config.app import Settings


logger = logging.getLogger("app.rate_limit")
settings = Settings()

# In-memory store: {identifier: [(timestamp, ...)]}
_rate_store: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limit requests per user/IP based on their configured limit."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and static files
        if request.url.path in ("/health", "/metrics") or request.url.path.startswith("/chat/"):
            return await call_next(request)

        identifier = await self._get_identifier(request)
        limit = self._get_limit(identifier)

        if limit is None:
            # Unknown user — use default global limit
            limit = settings.RATE_LIMIT_PER_MINUTE

        now = time.time()
        window_start = now - 60

        # Clean old entries
        _rate_store[identifier] = [t for t in _rate_store[identifier] if t > window_start]

        if len(_rate_store[identifier]) >= limit:
            logger.warning("Rate limit exceeded for %s (%d/min)", identifier, limit)
            return Response(
                status_code=429,
                content=(
                    '{"error":{"code":429,"message":"Rate limit exceeded. '
                    f'Maximum {limit} requests per minute.","type":"rate_limit"}}'
                ),
                media_type="application/json",
                headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)},
            )

        _rate_store[identifier].append(now)
        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(limit - len(_rate_store[identifier]))
        return response

    async def _get_identifier(self, request: Request) -> str:
        """Extract user identifier from JWT, API key, or IP."""
        auth_header = request.headers.get("Authorization", "")
        api_key_header = request.headers.get("X-API-Key", "")

        # Try JWT
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_access_token(token)
            if payload:
                return f"user:{payload.get('sub', 'unknown')}"

        # Try API key
        if api_key_header:
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.api_key == api_key_header).first()
                if user:
                    return f"user:{user.id}"
            finally:
                db.close()

        # Fall back to IP
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _get_limit(self, identifier: str) -> int | None:
        """Get per-user rate limit from database."""
        if identifier.startswith("user:"):
            try:
                user_id = int(identifier.split(":", 1)[1])
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        return user.rate_limit_per_minute
                finally:
                    db.close()
            except (ValueError, IndexError):
                pass
        return None
