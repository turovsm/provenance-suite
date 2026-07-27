import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.application.exceptions import (
    AlbumNotFoundError,
    ApplicationError,
    InvalidCredentialsError,
    StorageUploadError,
    UserAlreadyExistsError,
    UserDeactivatedError,
)
from src.domain.exceptions import DomainError
from src.presentation.schemas.error import ErrorDetailSchema, ErrorResponseEnvelope


logger = logging.getLogger("provenance.exceptions")


def create_error_response(
    status_code: int, code: str, message: str, details: Any = None
) -> JSONResponse:
    payload = ErrorResponseEnvelope(
        status="error",
        error=ErrorDetailSchema(code=code, message=message, details=details),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AlbumNotFoundError)
    async def album_not_found_handler(_request: Request, exc: AlbumNotFoundError) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_404_NOT_FOUND,
            code="ALBUM_NOT_FOUND",
            message=str(exc),
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        _request: Request, exc: InvalidCredentialsError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_CREDENTIALS",
            message=str(exc),
        )

    @app.exception_handler(UserDeactivatedError)
    async def user_deactivated_handler(
        _request: Request, exc: UserDeactivatedError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="ACCOUNT_SUSPENDED",
            message=str(exc),
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(
        _request: Request, exc: UserAlreadyExistsError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="IDENTITY_CONFLICT",
            message=str(exc),
        )

    @app.exception_handler(StorageUploadError)
    async def storage_upload_handler(_request: Request, exc: StorageUploadError) -> JSONResponse:
        logger.error("Object storage operation failure: %s", exc)
        return create_error_response(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code="STORAGE_ENGINE_FAILURE",
            message=str(exc),
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="DOMAIN_INVARIANT_VIOLATION",
            message=str(exc),
        )

    @app.exception_handler(ApplicationError)
    async def generic_application_error_handler(
        _request: Request, exc: ApplicationError
    ) -> JSONResponse:
        return create_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="APPLICATION_EXECUTION_ERROR",
            message=str(exc),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        formatted_errors = [
            {"field": " -> ".join(str(loc) for loc in err["loc"]), "msg": err["msg"]}
            for err in exc.errors()
        ]
        return create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_FAILED",
            message="Inbound request payload failed structural schema validation.",
            details=formatted_errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return create_error_response(
            status_code=exc.status_code,
            code="HTTP_ERROR",
            message=str(exc.detail),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled internal server exception processing path %s: %s", request.url.path, exc
        )
        return create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected infrastructure or system error occurred.",
        )
