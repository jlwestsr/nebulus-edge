"""Audit middleware for Nebulus Edge services.

This middleware enriches requests with audit context (request_id, session_id, user_id, etc.)
and adds audit headers to responses. It provides automatic tracking for all requests without
requiring explicit logging calls in routes.
"""

import hashlib
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware that enriches requests with audit context.

    This middleware:
    - Generates unique request_id for tracking
    - Extracts user_id and session_id from Open WebUI headers
    - Captures client IP address
    - Computes SHA-256 hashes of request/response bodies
    - Tracks request duration
    - Adds audit headers to responses

    The enriched context is stored in request.state and can be accessed by:
    - Route handlers for explicit audit logging
    - Other middleware or dependencies
    """

    def __init__(
        self,
        app,
        enabled: bool = True,
        debug: bool = False,
        default_user: str = "appliance-admin",
    ):
        """Initialize audit middleware.

        Args:
            app: FastAPI application
            enabled: Enable/disable audit context enrichment
            debug: Enable debug mode (logs full bodies)
            default_user: Default user_id when headers are missing
        """
        super().__init__(app)
        self.enabled = enabled
        self.debug = debug
        self.default_user = default_user

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and enrich with audit context."""
        if not self.enabled:
            return await call_next(request)

        # Generate unique request ID
        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Extract user and session from Open WebUI headers (fallback to defaults)
        user_id = request.headers.get("X-User-ID", self.default_user)
        session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))

        # Extract client IP (handle proxy headers)
        ip_address = request.headers.get(
            "X-Forwarded-For",
            request.headers.get("X-Real-IP", request.client.host if request.client else "unknown"),
        )
        # If X-Forwarded-For contains multiple IPs, take the first (client)
        if "," in ip_address:
            ip_address = ip_address.split(",")[0].strip()

        # Read request body for hashing
        request_body = await request.body()
        request_hash = self._hash_content(request_body)

        # Store full body only if debug mode is enabled
        request_body_stored = request_body.decode("utf-8", errors="replace") if self.debug else None

        # Enrich request.state with audit context
        request.state.request_id = request_id
        request.state.session_id = session_id
        request.state.user_id = user_id
        request.state.ip_address = ip_address
        request.state.timestamp = start_time
        request.state.request_hash = request_hash
        request.state.request_body = request_body_stored

        # Process request
        response = await call_next(request)

        # Compute response hash
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        response_hash = self._hash_content(response_body)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Store response context in request.state (for route-level audit logging)
        request.state.response_hash = response_hash
        request.state.duration_ms = duration_ms
        request.state.response_body = (
            response_body.decode("utf-8", errors="replace") if self.debug else None
        )

        # Add audit headers to response
        headers = dict(response.headers)
        headers["X-Request-ID"] = request_id
        headers["X-Audit-Timestamp"] = str(int(start_time))

        # Recreate response with enriched headers and body
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=headers,
            media_type=response.media_type,
        )

    def _hash_content(self, content: bytes) -> str:
        """Compute SHA-256 hash of content.

        Args:
            content: Raw bytes to hash

        Returns:
            Hexadecimal digest of SHA-256 hash
        """
        return hashlib.sha256(content).hexdigest()
