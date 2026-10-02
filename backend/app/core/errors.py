"""Application error types and the handlers that render them in the API envelope."""

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def error_body(message: str, data: Any = None) -> dict[str, Any]:
    """Build the failure half of the standard envelope."""
    return {"success": False, "message": message, "data": data}


class AppError(Exception):
    """Base class for errors that should surface as a clean JSON envelope."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class ValidationError(AppError):
    # Literal 422: Starlette renamed its constant and warns on the old name.
    status_code = 422
    code = "validation_error"


class BusinessRuleError(AppError):
    """A request that is well-formed but not allowed, e.g. insufficient funds."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "business_rule_violation"


def _flatten_validation_errors(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = [str(p) for p in err.get("loc", []) if p not in ("body", "query", "path")]
        field = ".".join(loc) or "request"
        parts.append(f"{field}: {err.get('msg', 'invalid value')}")
    return "; ".join(parts) or "Request validation failed"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(exc.message, {"code": exc.code}),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=error_body(
                _flatten_validation_errors(exc),
                {"code": "validation_error", "errors": exc.errors()},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(detail, {"code": code}),
        )

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Let the server logs keep the traceback; never leak internals to clients.
        import logging

        logging.getLogger("app").exception("Unhandled error", exc_info=exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_body("Internal server error", {"code": "internal_error"}),
        )