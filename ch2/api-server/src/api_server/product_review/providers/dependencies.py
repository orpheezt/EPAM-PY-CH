from typing import Annotated

from fastapi import Depends

from api_server.config import Provider, get_provider

from .config import get_hf_settings
from .hf import HFSentimentProvider, HFSummarizerProvider
from .protocols import SentimentProvider, SummarizerProvider


def get_sentiment_provider(
    provider_type: Annotated[Provider, Depends(get_provider)],
) -> SentimentProvider:
    match provider_type:
        case Provider.HF_API:
            return HFSentimentProvider(settings=get_hf_settings())
        case _:
            return HFSentimentProvider(settings=get_hf_settings())


def get_summarizer_provider(
    provider_type: Annotated[Provider, Depends(get_provider)],
) -> SummarizerProvider:
    match provider_type:
        case Provider.HF_API:
            return HFSummarizerProvider(settings=get_hf_settings())
        case _:
            return HFSummarizerProvider(settings=get_hf_settings())
