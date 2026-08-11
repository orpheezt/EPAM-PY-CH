from fastapi import Request, status
from fastapi.responses import JSONResponse

from .errors import AskError, HFInferenceError, VectorStoreError


async def on_ask_error(request: Request, exc: AskError) -> JSONResponse:
    match exc:
        case VectorStoreError():
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        case HFInferenceError():
            status_code = status.HTTP_502_BAD_GATEWAY
        case _:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )
