import logging
from collections.abc import Awaitable, Callable

from api_server.config import Provider

from .schemas import (
    BatchFeedbackResponse,
    FeedbackResponse,
    SentimentDetail,
    SentimentLabel,
)

type ProviderHandler = Callable[[list[str]], Awaitable[FeedbackResponse]]


class InferenceService:
    def __init__(
        self,
        provider: Provider,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.provider = provider
        self.handler: ProviderHandler

        match self.provider:
            case Provider.LITSERVE:
                self.handler = self._call_litserve
            case Provider.MODAL:
                self.handler = self._call_modal
            case Provider.HF_API:
                self.handler = self._call_hf_api

    async def dispatch_analyze(self, review: str) -> FeedbackResponse:
        return FeedbackResponse(
            sentiment=SentimentDetail(
                text="", label=SentimentLabel.POSITIVE, score=0.9
            ),
            summary="",
        )

    async def dispatch_analyze_batch(self, reviews: list[str]) -> BatchFeedbackResponse:
        return BatchFeedbackResponse(
            total_reviews=len(reviews),
            negative_count=0,
            sentiments=[
                SentimentDetail(text="", label=SentimentLabel.POSITIVE, score=0.9)
                for _ in reviews
            ],
            executive_summary="",
        )

    async def _call_litserve(self, reviews: list[str]):
        pass

    async def _call_modal(self, reviews: list[str]):
        pass

    async def _call_hf_api(self, reviews: list[str]):
        pass
