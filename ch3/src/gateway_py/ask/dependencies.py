from typing import Annotated

from fastapi import Depends

from .service import AskService
from .settings import AskSettings


def get_ask_settings() -> AskSettings:
    return AskSettings()


def get_ask_service(
    settings: Annotated[AskSettings, Depends(get_ask_settings)],
) -> AskService:
    return AskService(settings=settings)


AskServiceDep = Annotated[AskService, Depends(get_ask_service)]
