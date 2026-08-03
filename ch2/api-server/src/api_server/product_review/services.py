import asyncio
import logging

from .providers import SentimentProvider, SummarizerProvider
from .schemas import (
    BatchFeedbackResponse,
    FeedbackResponse,
    SentimentLabel,
)


class InferenceService:
    def __init__(
        self,
        sentiment_provider: SentimentProvider,
        summarizer_provider: SummarizerProvider,
        *,
        logger: logging.Logger | None = None,
    ) -> None:
        self.sentiment_provider = sentiment_provider
        self.summarizer_provider = summarizer_provider
        self.logger = logger or logging.getLogger(__name__)

    async def dispatch_analyze(self, review: str) -> FeedbackResponse:
        sentiments = await self.sentiment_provider.analyze_sentiment([review])
        return FeedbackResponse(sentiment=sentiments[0])

    async def dispatch_analyze_batch(self, reviews: list[str]) -> BatchFeedbackResponse:
        sent_task = self.sentiment_provider.analyze_sentiment(reviews)
        sum_task = self.summarizer_provider.generate_summary(reviews)

        sentiments, exec_summary = await asyncio.gather(sent_task, sum_task)
        neg_count = sum(1 for s in sentiments if s.label == SentimentLabel.NEGATIVE)

        return BatchFeedbackResponse(
            total_reviews=len(reviews),
            negative_count=neg_count,
            sentiments=sentiments,
            executive_summary=exec_summary,
        )
