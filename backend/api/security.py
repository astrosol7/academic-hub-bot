from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


@dataclass(frozen=True)
class RateLimitRule:
    window_seconds: int
    max_requests: int


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Lightweight in-memory rate limiter.
    This is a high-assurance *baseline* for local/single-node deployments.
    For multi-node scale, swap this for Redis-based limiting.
    """

    def __init__(self, app, rules: dict[str, RateLimitRule]):
        super().__init__(app)
        self.rules = rules
        self.buckets: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        # if behind a proxy, set proper forwarded headers at the edge
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        rule = None
        for prefix, r in self.rules.items():
            if path.startswith(prefix):
                rule = r
                break

        if rule:
            now = time.time()
            key = (self._client_key(request), prefix)
            q = self.buckets[key]

            # expire old entries
            cutoff = now - rule.window_seconds
            while q and q[0] < cutoff:
                q.popleft()

            if len(q) >= rule.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={"Retry-After": str(rule.window_seconds)},
                )
            q.append(now)

        return await call_next(request)

