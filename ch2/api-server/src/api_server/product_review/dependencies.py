from typing import Annotated

from fastapi import Depends

from .providers import (
    SentimentProvider,
    SummarizerProvider,
    get_sentiment_provider,
    get_summarizer_provider,
)
from .services import InferenceService


def get_inference_service(
    sentiment_provider: Annotated[SentimentProvider, Depends(get_sentiment_provider)],
    summarizer_provider: Annotated[
        SummarizerProvider, Depends(get_summarizer_provider)
    ],
) -> InferenceService:
    return InferenceService(
        sentiment_provider=sentiment_provider,
        summarizer_provider=summarizer_provider,
    )
