import logging
import time
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records incoming requests and logs execution duration.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        path = request.url.path
        if request.query_params:
            path += f"?{request.query_params}"

        logger.debug(f"Incoming request: {request.method} {path}")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"Status: {response.status_code} in {process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"Error: {str(e)} in {process_time:.4f}s",
                exc_info=True
            )
            raise e


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware attaching production security headers to all HTTP responses.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; "
            "font-src 'self' https: data: https://fonts.gstatic.com;"
        )
        return response


def register_middleware(app: FastAPI) -> None:
    """
    Hooks up middlewares to the FastAPI application.
    In FastAPI, middlewares added later wrap around outer handlers.
    """
    # Logging Middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # CORS Middleware (Registered outer-most to ensure preflight & error responses receive CORS headers)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
