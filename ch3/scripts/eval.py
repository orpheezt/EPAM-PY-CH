#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "httpx2>=2.9.1",
#     "pydantic-settings>=2.15.0",
#     "rich>=15.0.0",
#     "typer>=0.27.1",
# ]
# ///

import json
from pathlib import Path
from typing import Annotated

import httpx2
import typer
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(add_completion=False)
console = Console()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class EvalSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    server_url: str = Field(
        default="http://localhost:8000/ask/", validation_alias="GATEWAY_URL"
    )
    output_file: Path = PROJECT_ROOT / "evaluation_results.json"


TEST_DATASET = [
    {
        "question": "What is the primary role of One-Shot Bufferize in MLIR?",
        "ground_truth": "One-Shot Bufferize is a comprehensive bufferization module in MLIR designed to convert tensor-based operations into memref-based operations in a single analysis and transformation pass.",
    },
    {
        "question": "How does tensor-to-memref lowering work in Linalg?",
        "ground_truth": "Tensor-to-memref lowering in Linalg allocates memory buffers for tensor operands and replaces tensor-level operations with explicit memory reference manipulations.",
    },
    {
        "question": "What are the key architectural features of Rust's async runtime tokio?",
        "ground_truth": "I am sorry, but the provided documentation does not contain enough information to answer this question.",
    },
]


@app.command()
def run(
    server_url: Annotated[
        str, typer.Option(help="FastAPI Gateway /ask/ endpoint URL")
    ] = "http://localhost:8000/ask/",
) -> None:
    settings = EvalSettings(server_url=server_url)

    console.print(
        Panel.fit(
            f"[bold cyan]AUTOMATED RAG EVALUATION SUITE[/]\n"
            f"Target Endpoint: [yellow]{settings.server_url}[/]\n"
            f"Output Destination: [yellow]{settings.output_file}[/]",
            title="FastAPI Gateway RAG Evaluation",
            border_style="blue",
        )
    )

    eval_records = []

    console.print(
        f"Triggering [bold cyan]{len(TEST_DATASET)}[/] queries against Gateway..."
    )

    with httpx2.Client(timeout=None) as client:
        for idx, item in enumerate(TEST_DATASET, start=1):
            q = item["question"]
            gt = item["ground_truth"]
            console.print(
                f"  [[bold green]{idx}/{len(TEST_DATASET)}[/]] Querying: [dim]'{q}'[/]..."
            )

            try:
                res = client.post(settings.server_url, json={"question": q})
                res.raise_for_status()
                data = res.json()
                answer = data.get("answer", "")
                sources = data.get("sources", [])
                ctx_docs = data.get("context_docs", [])
            except (httpx2.HTTPError, httpx2.RequestError) as e:
                console.print(f"    [bold red]Error querying gateway endpoint:[/] {e}")
                answer = f"Error: {e}"
                sources = []
                ctx_docs = []

            eval_records.append(
                {
                    "question": q,
                    "answer": answer,
                    "sources": sources,
                    "ground_truth": gt,
                    "retrieved_context_chunks": len(ctx_docs),
                }
            )

    metrics_summary = {
        "total_queries": len(TEST_DATASET),
        "successful_responses": len(
            [r for r in eval_records if not r["answer"].startswith("Error")]
        ),
        "citation_count": sum(len(r["sources"]) for r in eval_records),
    }

    output_payload = {"metrics": metrics_summary, "test_results": eval_records}
    with open(settings.output_file, "w", encoding="utf-8") as f:
        json.dump(output_payload, f, indent=2)

    console.print(
        f"\n[bold green]Success![/] Saved evaluation output to [cyan]{settings.output_file}[/]\n"
    )

    table = Table(
        title="Evaluation Query Results", show_header=True, header_style="bold magenta"
    )
    table.add_column("Question", style="cyan", no_wrap=False)
    table.add_column("Sources", style="yellow")
    table.add_column("Status", style="green")

    for rec in eval_records:
        src_str = (
            ", ".join(rec["sources"])
            if isinstance(rec["sources"], list) and rec["sources"]
            else "None (Fallback)"
        )
        ans_str = str(rec.get("answer", ""))
        match (rec["sources"], "sorry" in ans_str):
            case (srcs, _) if srcs:
                status_str = "OK"
            case (_, True):
                status_str = "OK"
            case _:
                status_str = "Response Received"
        table.add_row(str(rec["question"]), src_str, status_str)

    console.print(table)


if __name__ == "__main__":
    app()
