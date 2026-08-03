import asyncio

import httpx

from api_server.product_review.schemas import SentimentDetail, SentimentLabel

from .config import HFSettings


def normalize_label(raw_label: str) -> SentimentLabel:
    match raw_label.upper():
        case "POS" | "POSITIVE" | "LABEL_2":
            return SentimentLabel.POSITIVE
        case "NEG" | "NEGATIVE" | "LABEL_0":
            return SentimentLabel.NEGATIVE
        case _:
            return SentimentLabel.NEUTRAL


class HFSentimentProvider:
    def __init__(
        self,
        settings: HFSettings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or httpx.AsyncClient()

    async def _analyze_single(
        self, review: str, headers: dict[str, str]
    ) -> SentimentDetail:
        resp = await self.client.post(
            self.settings.HF_SENTIMENT_API_URL,
            headers=headers,
            json={"inputs": review},
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        match data:
            case (
                [[{"label": label, "score": score}, *_], *_]
                | [{"label": label, "score": score}, *_]
                | {"label": label, "score": score}
            ):
                return SentimentDetail(
                    text=review,
                    label=normalize_label(str(label)),
                    score=float(score),
                )
            case _:
                raise ValueError(f"Unexpected response format from HF API: {data}")

    async def analyze_sentiment(self, reviews: list[str]) -> list[SentimentDetail]:
        headers: dict[str, str] = {}
        if self.settings.HF_TOKEN:
            headers["Authorization"] = f"Bearer {self.settings.HF_TOKEN}"

        tasks = [self._analyze_single(r, headers) for r in reviews]
        return list(await asyncio.gather(*tasks))


class HFSummarizerProvider:
    def __init__(
        self,
        settings: HFSettings,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or httpx.AsyncClient()

    async def generate_summary(self, reviews: list[str]) -> str:
        headers: dict[str, str] = {}
        if self.settings.HF_TOKEN:
            headers["Authorization"] = f"Bearer {self.settings.HF_TOKEN}"

        text = " ".join(reviews).strip()
        if not text:
            return ""
        if len(text) < 60:
            return text

        if len(text) > 3000:
            text = text[:3000].rsplit(" ", 1)[0]

        resp = await self.client.post(
            self.settings.HF_SUMMARIZER_API_URL,
            headers=headers,
            json={
                "inputs": text,
                "parameters": {"max_length": 60, "min_length": 10},
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        match data:
            case [{"summary_text": summary}, *_]:
                return str(summary).strip()
            case {"summary_text": summary}:
                return str(summary).strip()
            case _:
                return text
