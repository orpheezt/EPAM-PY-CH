#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "datasets>=5.0.1",
#     "httpx2>=2.9.1",
#     "rich>=15.0.0",
#     "typer>=0.27.0",
# ]
# ///
"""Test API server feedback endpoints using amazon_reviews_multi dataset."""

import asyncio
import time
from dataclasses import dataclass
from typing import Annotated

import httpx2
import typer
from datasets import load_dataset
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


@dataclass(frozen=True)
class ReviewSample:
    rating: str
    star: int
    text: str


app = typer.Typer(
    help="Test API server feedback endpoints using amazon_reviews_multi (English)",
    add_completion=False,
)
console = Console()


def get_rating_name(star: int) -> str:
    match star:
        case 0:
            return "1-Star (Very Negative)"
        case 1:
            return "2-Star (Negative)"
        case 2:
            return "3-Star (Neutral)"
        case 3:
            return "4-Star (Positive)"
        case 4:
            return "5-Star (Very Positive)"
        case _:
            return f"{star + 1}-Star"


async def run_tests(base_url: str, samples_per_star: int) -> None:
    console.print(
        Panel.fit(
            f"[bold green]Target URL:[/] [white]{base_url}[/]\n"
            f"[bold green]Dataset:[/]    [white]SetFit/amazon_reviews_multi_en (test split)[/]\n"
            f"[bold green]Samples:[/]    [white]{samples_per_star} per rating level (total {samples_per_star * 5})[/]",
            title="[bold cyan]AMAZON REVIEWS LIVE API TEST[/]",
            border_style="blue",
        )
    )

    with console.status("[bold green]Loading dataset from Hugging Face Hub..."):
        dataset = load_dataset("SetFit/amazon_reviews_multi_en", split="test")

    samples: list[ReviewSample] = []
    for star in range(5):
        star_items = [item for item in dataset if item["label"] == star][
            :samples_per_star
        ]
        for item in star_items:
            samples.append(
                ReviewSample(
                    rating=get_rating_name(star),
                    star=star,
                    text=str(item["text"]),
                )
            )

    async with httpx2.AsyncClient(base_url=base_url, timeout=30.0) as client:
        try:
            h_resp = await client.get("/health")
            console.print(
                f"[bold green]✓ Server Healthcheck:[/] [white]{h_resp.json()}[/]\n"
            )
        except httpx2.HTTPError as e:

            console.print(f"[bold red]✗ Could not reach server at {base_url}:[/] {e}")
            raise typer.Exit(code=1)

        console.print(
            "[bold underline]1. Testing /analyze-feedback (Single Reviews)[/]"
        )
        single_table = Table(show_header=True, header_style="bold magenta")
        single_table.add_column("Rating Category", style="cyan")
        single_table.add_column("Review Snippet", style="white")
        single_table.add_column("Predicted Label", style="yellow")
        single_table.add_column("Score", justify="right", style="green")
        single_table.add_column("Latency", justify="right", style="blue")

        for sample in samples[:5]:
            text = sample.text
            t0 = time.perf_counter()
            resp = await client.post("/analyze-feedback", json={"review": text})
            elapsed = (time.perf_counter() - t0) * 1000

            match resp.status_code:
                case 200:
                    data = resp.json()
                    sent = data["sentiment"]
                    single_table.add_row(
                        sample.rating,
                        f"{text[:45]}...",
                        str(sent["label"]),
                        f"{sent['score']:.4f}",
                        f"{elapsed:.1f} ms",
                    )
                case status_code:
                    single_table.add_row(
                        sample.rating,
                        f"{text[:45]}...",
                        f"[red]ERR {status_code}[/]",
                        "N/A",
                        f"{elapsed:.1f} ms",
                    )

        console.print(single_table)
        console.print()

        console.print(
            "[bold underline]2. Testing /analyze-feedback/batch (Batch Analysis)[/]"
        )
        batch_texts = [s.text for s in samples]
        t0 = time.perf_counter()
        resp_batch = await client.post(
            "/analyze-feedback/batch", json={"reviews": batch_texts}
        )
        batch_elapsed = (time.perf_counter() - t0) * 1000

        match resp_batch.status_code:
            case 200:
                bdata = resp_batch.json()
                console.print(
                    f"Total Reviews:     [bold cyan]{bdata['total_reviews']}[/]"
                )
                console.print(
                    f"Negative Count:    [bold red]{bdata['negative_count']}[/]"
                )
                console.print(
                    f"Batch Processing:  [bold green]{batch_elapsed:.1f} ms[/]"
                )
                console.print(
                    f'Executive Summary: [yellow]"{bdata["executive_summary"]}"[/]'
                )
            case status_code:
                console.print(
                    f"[bold red]Batch analysis failed ({status_code}):[/] {resp_batch.text}"
                )


@app.command()
def main(
    base_url: Annotated[
        str,
        typer.Option(
            "--base-url",
            "-b",
            help="Base URL of the running API server",
        ),
    ] = "http://127.0.0.1:8000",
    samples_per_star: Annotated[
        int,
        typer.Option(
            "--samples-per-star",
            "-s",
            help="Number of samples to evaluate per star rating level (1-5)",
        ),
    ] = 2,
) -> None:
    asyncio.run(run_tests(base_url.rstrip("/"), samples_per_star))


if __name__ == "__main__":
    app()
