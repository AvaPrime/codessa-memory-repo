from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from codessa_memory.limits.service import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        *,
        limiter: RateLimiter,
        enabled: bool,
        public_prefixes: Iterable[str],
    ) -> None:
        super().__init__(app)
        self.limiter = limiter
        self.enabled = enabled
        self.public_prefixes = tuple(public_prefixes)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        if not self.enabled:
            return await call_next(request)

        path = request.url.path
        if any(path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in self.public_prefixes):
            return await call_next(request)

        key = request.client.host if request.client else "unknown"
        allowed, retry_after = self.limiter.check(key)
        if not allowed:
            headers = {"Retry-After": str(retry_after)}
            return JSONResponse({"detail": "Rate limit exceeded"}, status_code=HTTP_429_TOO_MANY_REQUESTS, headers=headers)
        return await call_next(request)
