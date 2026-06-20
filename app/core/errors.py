from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorResponse(BaseModel):
    error: str
    message: str
    request_id: str | None = None


class NotFoundError(Exception):
    def __init__(self, detail: str = "Resource not found") -> None:
        self.detail = detail


class ValidationError_(Exception):
    def __init__(self, detail: str = "Validation failed") -> None:
        self.detail = detail


def _request_id(request: Request) -> str | None:
    return request.headers.get("x-request-id")


def _error_response(
    request: Request,
    status_code: int,
    error: str,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=error,
            message=message,
            request_id=_request_id(request),
        ).model_dump(),
    )


def _validation_message(errors: list[dict[str, Any]]) -> str:
    messages: list[str] = []
    for item in errors:
        loc = ".".join(str(part) for part in item.get("loc", []) if part != "body")
        message = item.get("msg", "Invalid value")
        messages.append(f"{loc}: {message}" if loc else message)
    return "; ".join(messages) or "Validation failed"


def register_error_handlers(app) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
        return _error_response(request, 404, "not_found", exc.detail)

    @app.exception_handler(ValidationError_)
    async def validation_error_handler(request: Request, exc: ValidationError_) -> JSONResponse:
        return _error_response(request, 422, "validation_error", exc.detail)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(request, 422, "validation_error", _validation_message(exc.errors()))

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        error = "not_found" if exc.status_code == 404 else "http_error"
        if exc.status_code == 422:
            error = "validation_error"
        return _error_response(request, exc.status_code, error, detail)

    @app.exception_handler(Exception)
    async def general_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return _error_response(request, 500, "internal_error", "An unexpected error occurred.")
