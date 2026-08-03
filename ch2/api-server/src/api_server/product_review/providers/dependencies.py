from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from api_server.config import Provider, Settings, get_provider, get_settings

from .cached import CachedSentimentProvider
from .config import get_hf_settings
from .hf import HFSentimentProvider, HFSummarizerProvider
from .protocols import SentimentProvider, SummarizerProvider


def _create_base_sentiment_provider(provider_type: Provider) -> SentimentProvider:
    match provider_type:
        case Provider.HF_API | Provider.LITSERVE | Provider.MODAL:
            return HFSentimentProvider(settings=get_hf_settings())
        case _:
            return HFSentimentProvider(settings=get_hf_settings())


@lru_cache
def _get_cached_sentiment_provider(
    provider_type: Provider,
    ttl_seconds: int,
    max_size: int,
) -> CachedSentimentProvider:
    base_provider = _create_base_sentiment_provider(provider_type)
    return CachedSentimentProvider(
        provider=base_provider,
        ttl_seconds=ttl_seconds,
        max_size=max_size,
    )


def get_sentiment_provider(
    provider_type: Annotated[Provider, Depends(get_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> SentimentProvider:
    if not settings.CACHE_ENABLED:
        return _create_base_sentiment_provider(provider_type)

    return _get_cached_sentiment_provider(
        provider_type=provider_type,
        ttl_seconds=settings.CACHE_TTL_SECONDS,
        max_size=settings.CACHE_MAX_SIZE,
    )


def get_summarizer_provider(
    provider_type: Annotated[Provider, Depends(get_provider)],
) -> SummarizerProvider:
    match provider_type:
        case Provider.HF_API | Provider.LITSERVE | Provider.MODAL:
            return HFSummarizerProvider(settings=get_hf_settings())
        case _:
            return HFSummarizerProvider(settings=get_hf_settings())


