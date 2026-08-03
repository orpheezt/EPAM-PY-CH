import asyncio
from unittest.mock import AsyncMock

import pytest

from api_server.product_review.providers.cached import CachedSentimentProvider
from api_server.product_review.schemas import SentimentDetail, SentimentLabel


@pytest.fixture
def mock_base_provider():
    provider = AsyncMock()

    async def side_effect(reviews: list[str]) -> list[SentimentDetail]:
        return [
            SentimentDetail(text=r, label=SentimentLabel.POSITIVE, score=0.99)
            for r in reviews
        ]

    provider.analyze_sentiment.side_effect = side_effect
    return provider


@pytest.mark.asyncio
async def test_cache_hit_prevents_duplicate_provider_calls(mock_base_provider):
    cached_provider = CachedSentimentProvider(
        provider=mock_base_provider, ttl_seconds=3600, max_size=100
    )

    # First call - cache miss
    res1 = await cached_provider.analyze_sentiment(["Great product!"])
    assert len(res1) == 1
    assert mock_base_provider.analyze_sentiment.call_count == 1
    assert mock_base_provider.analyze_sentiment.call_args[0][0] == ["Great product!"]

    # Second call - cache hit
    res2 = await cached_provider.analyze_sentiment(["Great product!"])
    assert len(res2) == 1
    assert res2[0].text == "Great product!"
    # Call count to base provider should remain 1
    assert mock_base_provider.analyze_sentiment.call_count == 1


@pytest.mark.asyncio
async def test_partial_cache_hit(mock_base_provider):
    cached_provider = CachedSentimentProvider(
        provider=mock_base_provider, ttl_seconds=3600, max_size=100
    )

    # Pre-cache "Review 1"
    await cached_provider.analyze_sentiment(["Review 1"])
    assert mock_base_provider.analyze_sentiment.call_count == 1

    mock_base_provider.analyze_sentiment.reset_mock()

    # Call with "Review 1" (cached) and "Review 2" (uncached)
    res = await cached_provider.analyze_sentiment(["Review 1", "Review 2"])
    assert len(res) == 2
    assert res[0].text == "Review 1"
    assert res[1].text == "Review 2"

    # Underlying provider should only be called for "Review 2"
    assert mock_base_provider.analyze_sentiment.call_count == 1
    assert mock_base_provider.analyze_sentiment.call_args[0][0] == ["Review 2"]


@pytest.mark.asyncio
async def test_cache_ttl_expiration(mock_base_provider):
    cached_provider = CachedSentimentProvider(
        provider=mock_base_provider, ttl_seconds=0.1, max_size=100
    )

    await cached_provider.analyze_sentiment(["Expiring review"])
    assert mock_base_provider.analyze_sentiment.call_count == 1

    await asyncio.sleep(0.15)

    await cached_provider.analyze_sentiment(["Expiring review"])
    assert mock_base_provider.analyze_sentiment.call_count == 2


@pytest.mark.asyncio
async def test_cache_max_size_eviction(mock_base_provider):
    cached_provider = CachedSentimentProvider(
        provider=mock_base_provider, ttl_seconds=3600, max_size=2
    )

    await cached_provider.analyze_sentiment(["R1", "R2"])
    assert mock_base_provider.analyze_sentiment.call_count == 1

    # Insert R3, evicting R1
    await cached_provider.analyze_sentiment(["R3"])
    assert mock_base_provider.analyze_sentiment.call_count == 2

    mock_base_provider.analyze_sentiment.reset_mock()

    # R2 and R3 should be hits
    await cached_provider.analyze_sentiment(["R2", "R3"])
    assert mock_base_provider.analyze_sentiment.call_count == 0

    # R1 should be a miss (evicted)
    await cached_provider.analyze_sentiment(["R1"])
    assert mock_base_provider.analyze_sentiment.call_count == 1
