from fastapi import APIRouter, status

from .dependencies import AskServiceDep
from .schemas import AskRequest, AskResponse

router = APIRouter(tags=["ask"])


@router.post("/ask/", response_model=AskResponse, status_code=status.HTTP_200_OK)
@router.post(
    "/ask",
    response_model=AskResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def ask_question(
    payload: AskRequest,
    service: AskServiceDep,
) -> AskResponse:
    return await service.ask(payload.question)
