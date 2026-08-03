import httpx
import pytest

from api_server.product_review.providers.config import HFSettings
from api_server.product_review.providers.hf import (
    HFSentimentProvider,
    HFSummarizerProvider,
    normalize_label,
)
from api_server.product_review.schemas import SentimentLabel


def test_normalize_label():
    assert normalize_label("POS") == SentimentLabel.POSITIVE
    assert normalize_label("positive") == SentimentLabel.POSITIVE
    assert normalize_label("LABEL_2") == SentimentLabel.POSITIVE

    assert normalize_label("NEG") == SentimentLabel.NEGATIVE
    assert normalize_label("negative") == SentimentLabel.NEGATIVE
    assert normalize_label("LABEL_0") == SentimentLabel.NEGATIVE

    assert normalize_label("NEU") == SentimentLabel.NEUTRAL
    assert normalize_label("neutral") == SentimentLabel.NEUTRAL
    assert normalize_label("LABEL_1") == SentimentLabel.NEUTRAL
    assert normalize_label("UNKNOWN") == SentimentLabel.NEUTRAL


@pytest.mark.asyncio
async def test_hf_sentiment_provider_mock():
    def handle_request(request: httpx.Request) -> httpx.Response:
        import json

        data = json.loads(request.content.decode("utf-8"))
        inputs = data.get("inputs", "")
        if "Bad" in str(inputs):
            return httpx.Response(200, json=[[{"label": "NEG", "score": 0.88}]])
        return httpx.Response(200, json=[[{"label": "POS", "score": 0.95}]])

    transport = httpx.MockTransport(handle_request)

    settings = HFSettings(HF_TOKEN="test_token")

    async with httpx.AsyncClient(transport=transport) as client:
        provider = HFSentimentProvider(settings=settings, client=client)
        sentiments = await provider.analyze_sentiment(["Good", "Bad"])
        assert len(sentiments) == 2
        assert sentiments[0].label == SentimentLabel.POSITIVE
        assert sentiments[1].label == SentimentLabel.NEGATIVE


@pytest.mark.asyncio
async def test_hf_summarizer_provider_mock():
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[{"summary_text": "Resumen general de las reseñas."}],
        )

    transport = httpx.MockTransport(handle_request)

    settings = HFSettings(HF_TOKEN="test_token")

    async with httpx.AsyncClient(transport=transport) as client:
        provider = HFSummarizerProvider(settings=settings, client=client)
        summary = await provider.generate_summary(
            ["Excelente producto, la entrega fue muy rápida y la atención excelente."]
        )
        assert summary == "Resumen general de las reseñas."
