from typing import Annotated

from fastapi import APIRouter, Depends

from api_server import __version__
from api_server.config import Provider, get_provider
from api_server.healthcheck.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(
    provider: Annotated[Provider, Depends(get_provider)],
) -> HealthResponse:
    return HealthResponse(status="OK", inference_provider=provider, version=__version__)
