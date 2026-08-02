from enum import StrEnum

from pydantic import BaseModel


class SentimentLabel(StrEnum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class SentimentDetail(BaseModel):
    text: str
    label: SentimentLabel
    score: float


class FeedbackRequest(BaseModel):
    review: str


class BatchFeedbackRequest(BaseModel):
    reviews: list[str]


class FeedbackResponse(BaseModel):
    sentiment: SentimentDetail
    summary: str


class BatchFeedbackResponse(BaseModel):
    total_reviews: int
    negative_count: int
    sentiments: list[SentimentDetail]
    executive_summary: str


__all__ = [
    "BatchFeedbackRequest",
    "BatchFeedbackResponse",
    "FeedbackRequest",
    "FeedbackResponse",
    "SentimentDetail",
    "SentimentLabel",
]
