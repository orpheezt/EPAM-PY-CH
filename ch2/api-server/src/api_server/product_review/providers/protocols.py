from typing import Protocol

from api_server.product_review.schemas import SentimentDetail


class SentimentProvider(Protocol):
    async def analyze_sentiment(self, reviews: list[str]) -> list[SentimentDetail]: ...


class SummarizerProvider(Protocol):
    async def generate_summary(self, reviews: list[str]) -> str: ...
