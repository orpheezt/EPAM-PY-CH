from unittest.mock import AsyncMock

import httpx2
import pytest

from api_server.app import app
from api_server.config import get_settings
from api_server.product_review.dependencies import get_inference_service
from api_server.product_review.schemas import SentimentLabel


@pytest.fixture
def mock_inference_service():
    service = AsyncMock()
    service.dispatch_analyze.return_value = {
        "sentiment": {
            "text": "Great!",
            "label": SentimentLabel.POSITIVE,
            "score": 0.99,
        }
    }
    return service


@pytest.mark.asyncio
async def test_rate_limit_exceeded(mock_inference_service):
    app.dependency_overrides[get_inference_service] = lambda: mock_inference_service
    settings = get_settings()

    # Store original values
    orig_enabled = settings.RATE_LIMIT_ENABLED
    orig_limit = settings.RATE_LIMIT_PER_MINUTE
    settings.RATE_LIMIT_ENABLED = True
    settings.RATE_LIMIT_PER_MINUTE = 3

    try:
        transport = httpx2.ASGITransport(app=app)
        async with httpx2.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:

            # First 3 requests should succeed
            for _ in range(3):
                response = await client.post(
                    "/analyze-feedback", json={"review": "Good"}
                )
                assert response.status_code == 200

            # 4th request should be rate limited
            response = await client.post("/analyze-feedback", json={"review": "Good"})
            assert response.status_code == 429
            assert "Retry-After" in response.headers
            assert response.json()["detail"] == "Rate limit exceeded. Too many requests."

            # Excluded path /health should still work
            health_res = await client.get("/health")
            assert health_res.status_code == 200
    finally:
        settings.RATE_LIMIT_ENABLED = orig_enabled
        settings.RATE_LIMIT_PER_MINUTE = orig_limit
        app.dependency_overrides.clear()
