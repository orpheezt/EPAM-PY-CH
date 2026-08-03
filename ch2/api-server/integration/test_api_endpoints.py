from fastapi.testclient import TestClient

from api_server.app import app
from api_server.product_review.schemas import SentimentLabel


def test_api_endpoints_integration(monkeypatch):
    class MockSentimentProvider:
        async def analyze_sentiment(self, reviews: list[str]):
            from api_server.product_review.schemas import SentimentDetail

            return [
                SentimentDetail(text=r, label=SentimentLabel.POSITIVE, score=0.95)
                for r in reviews
            ]

    class MockSummarizerProvider:
        async def generate_summary(self, reviews: list[str]):
            return "Mock summary for reviews"

    from api_server.product_review.dependencies import (
        get_sentiment_provider,
        get_summarizer_provider,
    )

    app.dependency_overrides[get_sentiment_provider] = lambda: MockSentimentProvider()
    app.dependency_overrides[get_summarizer_provider] = lambda: MockSummarizerProvider()

    client = TestClient(app)

    try:
        resp = client.post("/analyze-feedback", json={"review": "Excelente producto"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["sentiment"]["label"] == "POSITIVE"
        assert "summary" not in data

        resp_batch = client.post(
            "/analyze-feedback/batch",
            json={"reviews": ["Excelente producto", "Muy bueno"]},
        )
        assert resp_batch.status_code == 200
        data_batch = resp_batch.json()
        assert data_batch["total_reviews"] == 2
        assert data_batch["negative_count"] == 0
        assert data_batch["executive_summary"] == "Mock summary for reviews"
    finally:
        app.dependency_overrides.clear()
