from typing import Annotated

from fastapi import Depends

from api_server.config import Provider, get_provider

from .services import InferenceService


def get_inference_service(
    provider: Annotated[Provider, Depends(get_provider)],
) -> InferenceService:
    return InferenceService(provider)
