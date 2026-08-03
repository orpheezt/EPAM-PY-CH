import time
from collections import OrderedDict

from api_server.product_review.schemas import SentimentDetail

from .protocols import SentimentProvider


class CachedSentimentProvider:
    """Decorator that adds in-memory TTL & capacity bounded caching to a SentimentProvider."""

    def __init__(
        self,
        provider: SentimentProvider,
        *,
        ttl_seconds: int = 3600,
        max_size: int = 1000,
    ) -> None:
        self.provider = provider
        self.ttl_seconds = ttl_seconds
        self.max_size = max_size
        self._cache: OrderedDict[str, tuple[SentimentDetail, float]] = OrderedDict()

    def _is_expired(self, timestamp: float, now: float) -> bool:
        return (now - timestamp) > self.ttl_seconds

    def _clean_expired(self, now: float) -> None:
        expired_keys = [
            key for key, (_, ts) in self._cache.items() if self._is_expired(ts, now)
        ]
        for key in expired_keys:
            del self._cache[key]

    async def analyze_sentiment(self, reviews: list[str]) -> list[SentimentDetail]:
        now = time.monotonic()
        self._clean_expired(now)

        results: list[SentimentDetail | None] = [None] * len(reviews)
        uncached_indices: list[int] = []
        uncached_reviews: list[str] = []

        for idx, review in enumerate(reviews):
            in_cache = review in self._cache
            ts = self._cache[review][1] if in_cache else 0.0
            match (in_cache, self._is_expired(ts, now)):
                case (True, False):
                    sentiment, _ = self._cache[review]
                    self._cache.move_to_end(review)
                    results[idx] = sentiment
                case (True, True):
                    del self._cache[review]
                    uncached_indices.append(idx)
                    uncached_reviews.append(review)
                case (False, _):
                    uncached_indices.append(idx)
                    uncached_reviews.append(review)


        if uncached_reviews:
            new_sentiments = await self.provider.analyze_sentiment(uncached_reviews)
            for idx, review, sentiment in zip(
                uncached_indices, uncached_reviews, new_sentiments, strict=True
            ):
                results[idx] = sentiment
                self._cache[review] = (sentiment, now)
                self._cache.move_to_end(review)

                while len(self._cache) > self.max_size:
                    self._cache.popitem(last=False)

        return [res for res in results if res is not None]
