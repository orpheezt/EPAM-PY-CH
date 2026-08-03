import time
from collections import defaultdict

from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse

from api_server.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        *,
        excluded_paths: set[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.excluded_paths = excluded_paths or {"/health", "/docs", "/openapi.json", "/redoc"}
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        match (request.headers.get("x-forwarded-for"), request.client):
            case (str(forwarded_for), _) if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            case (_, client) if client and client.host:
                return client.host
            case _:
                return "127.0.0.1"


    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        settings = get_settings()

        if not settings.RATE_LIMIT_ENABLED or request.url.path in self.excluded_paths:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.monotonic()
        window_seconds = 60.0

        # Clean timestamps older than 60 seconds
        timestamps = [
            ts for ts in self._requests[client_ip] if now - ts < window_seconds
        ]
        self._requests[client_ip] = timestamps

        if len(timestamps) >= settings.RATE_LIMIT_PER_MINUTE:
            oldest_ts = timestamps[0]
            retry_after = max(1, int(window_seconds - (now - oldest_ts)))
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Too many requests."},
                headers={"Retry-After": str(retry_after)},
            )

        self._requests[client_ip].append(now)
        return await call_next(request)
