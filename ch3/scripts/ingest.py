#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "fastembed>=0.5.0",
#     "gateway-py",
#     "langchain>=1.3.15",
#     "langchain-core>=1.5.0",
#     "langchain-qdrant>=1.1.0",
#     "langchain-text-splitters>=1.1.2",
#     "pydantic-settings>=2.15.0",
#     "qdrant-client[fastembed]>=1.19.0",
#     "rich>=15.0.0",
#     "typer>=0.27.1",
# ]
# [tool.uv.sources]
# gateway-py = { path = ".." }
# ///

from pathlib import Path
from typing import Annotated

import typer
from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from gateway_py.embeddings import FastEmbedEmbeddings

app = typer.Typer(add_completion=False)
console = Console()

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class IngestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    data_dir: Path = PROJECT_ROOT / "data"
    qdrant_path: Path = PROJECT_ROOT / "qdrant_db"
    qdrant_url: str = Field(default="", validation_alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", validation_alias="QDRANT_API_KEY")
    collection_name: str = "mlir_linalg_docs"
    chunk_size: int = 600
    chunk_overlap: int = 80


def load_markdown_documents(data_dir: Path) -> list[Document]:
    """Load markdown documents directly without deprecated loaders."""
    documents: list[Document] = []
    for filepath in sorted(data_dir.rglob("*.md")):
        if filepath.is_file():
            content = filepath.read_text(encoding="utf-8")
            documents.append(
                Document(
                    page_content=content,
                    metadata={"source": filepath.name},
                )
            )
    return documents


@app.command()
def ingest(
    data_dir: Annotated[
        Path, typer.Option(help="Path to data directory containing markdown files")
    ] = PROJECT_ROOT / "data",
) -> None:
    """Ingest technical documentation into Qdrant vector database."""
    settings = IngestSettings(data_dir=data_dir)

    console.print(
        Panel.fit(
            f"[bold cyan]DATA INGESTION PIPELINE[/]\n"
            f"Source Directory: [yellow]{settings.data_dir}[/]\n"
            f"Qdrant Target: [yellow]{settings.qdrant_url or settings.qdrant_path}[/]",
            title="Qdrant Knowledge Base Ingestion",
            border_style="green",
        )
    )

    if not settings.data_dir.exists():
        console.print(
            f"[bold red]Error:[/] Data directory {settings.data_dir} does not exist."
        )
        raise typer.Exit(code=1)

    console.print("[bold green]1/4[/] Loading markdown documents...")
    documents = load_markdown_documents(settings.data_dir)
    console.print(f"    Loaded [bold yellow]{len(documents)}[/] document files.")

    console.print("[bold green]2/4[/] Chunking text content...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    chunks = text_splitter.split_documents(documents)
    console.print(f"    Created [bold yellow]{len(chunks)}[/] text chunks.")

    console.print(
        "[bold green]3/4[/] Initializing FastEmbed & Qdrant vector storage..."
    )
    embeddings = FastEmbedEmbeddings()
    vector_dim = len(embeddings.embed_query("test"))

    if settings.qdrant_url:
        console.print(
            f"    Connecting to Qdrant Cloud at [cyan]{settings.qdrant_url}[/]..."
        )
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    else:
        console.print(
            f"    Connecting to local Qdrant path at [cyan]{settings.qdrant_path}[/]..."
        )
        client = QdrantClient(path=str(settings.qdrant_path))

    if client.collection_exists(settings.collection_name):
        console.print(
            f"    Recreating existing collection '[bold magenta]{settings.collection_name}[/]'..."
        )
        client.delete_collection(settings.collection_name)

    client.create_collection(
        collection_name=settings.collection_name,
        vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
    )

    console.print("[bold green]4/4[/] Indexing document chunks...")
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=settings.collection_name,
        embedding=embeddings,
    )
    vector_store.add_documents(chunks)

    table = Table(
        title="Ingestion Summary", show_header=True, header_style="bold magenta"
    )
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Document Files Ingested", str(len(documents)))
    table.add_row("Total Text Chunks Created", str(len(chunks)))
    table.add_row("Vector Dimension", str(vector_dim))
    table.add_row("Qdrant Collection", settings.collection_name)

    console.print(table)
    console.print(
        f"\n[bold green]Success![/] Ingested [bold]{len(chunks)}[/] chunks into Qdrant collection '[cyan]{settings.collection_name}[/]'."
    )


if __name__ == "__main__":
    app()
