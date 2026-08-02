from typing import Annotated

from fastapi import APIRouter, Depends, status

from .dependencies import get_inference_service
from .schemas import (
    BatchFeedbackRequest,
    BatchFeedbackResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from .services import InferenceService

router = APIRouter(tags=["Health"])


@router.post(
    "/analyze-feedback",
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def analyze_feedback(
    request: FeedbackRequest,
    service: Annotated[InferenceService, Depends(get_inference_service)],
) -> FeedbackResponse:
    return await service.dispatch_analyze(request.review)


@router.post(
    "/analyze-feedback/batch",
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def analyze_batch_feedback(
    request: BatchFeedbackRequest,
    service: Annotated[InferenceService, Depends(get_inference_service)],
) -> BatchFeedbackResponse:
    return await service.dispatch_analyze_batch(request.reviews)
