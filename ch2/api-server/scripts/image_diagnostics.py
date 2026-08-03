#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "rich>=15.0.0",
#     "typer>=0.27.0",
# ]
# ///
"""Container image size and layer breakdown diagnostics script."""

import json
import subprocess
from collections import Counter
from pathlib import Path
from shutil import which
from typing import Annotated, TypedDict

import typer
from rich.console import Console
from rich.filesize import decimal as fmt_decimal
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    help="Display container image size breakdown, archive stats & GPG signature",
    add_completion=False,
)
console = Console()


class SignatureInfo(TypedDict):
    status: str
    signer: str
    fingerprint: str


BASE_IMAGE_KEYWORDS = (
    "FROM",
    "debian",
    "buildkit",
    "python",
    "apt-get",
    "ENV PATH=/usr/local",
)


def get_history_data(image_ref: str) -> list[dict] | None:
    """Retrieve layer history and sizes using buildah inspect."""
    if not which("buildah"):
        return None

    res = subprocess.run(
        ["buildah", "inspect", "--type", "image", image_ref],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return None

    b_data = json.loads(res.stdout)
    history = b_data.get("History", [])
    manifest_raw = b_data.get("Manifest", "{}")
    match manifest_raw:
        case str():
            manifest = json.loads(manifest_raw)
        case _:
            manifest = manifest_raw
    layers = manifest.get("layers", [])

    h_list = []
    layer_idx = 0
    img_id = b_data.get("FromImageID", "N/A")[:12]
    for h in history:
        is_empty = h.get("empty_layer", False)
        sz = (
            layers[layer_idx]["size"]
            if (not is_empty and layer_idx < len(layers))
            else 0
        )
        if not is_empty:
            layer_idx += 1
        h_list.append(
            {
                "id": img_id,
                "Created": h.get("created", "N/A"),
                "CreatedBy": h.get("created_by", ""),
                "size": sz,
            }
        )
    return h_list


def inspect_gpg_signature(sig_file: Path, archive_file: Path) -> SignatureInfo:
    """Inspect and verify GPG signature file using pattern matching."""
    if not sig_file.exists() or not which("gpg"):
        return {"status": "UNSIGNED", "signer": "N/A", "fingerprint": "N/A"}

    res = subprocess.run(
        ["gpg", "--status-fd", "1", "--verify", str(sig_file), str(archive_file)],
        capture_output=True,
        text=True,
        check=False,
    )
    signer, fp, is_good = "N/A", "N/A", False
    for line in res.stdout.splitlines():
        match line.split():
            case ["[GNUPG:]", "GOODSIG", _, *signer_parts]:
                is_good = True
                signer = " ".join(signer_parts)
            case ["[GNUPG:]", "VALIDSIG", fingerprint, *_]:
                fp = fingerprint

    status = "VALID SIGNATURE" if is_good else "INVALID SIGNATURE"
    return {"status": status, "signer": signer, "fingerprint": fp}


def categorize_layers(history_data: list[dict]) -> Counter[str]:
    """Categorize layer sizes by command pattern using Counter and pattern matching."""
    totals: Counter[str] = Counter()
    for item in history_data:
        size = item.get("size", 0)
        cmd = item.get("CreatedBy", "") or ""
        match cmd:
            case c if "/app/.venv" in c:
                totals["venv"] += size
            case c if "/app/app-packages" in c:
                totals["app"] += size
            case c if any(k in c for k in BASE_IMAGE_KEYWORDS):
                totals["base"] += size
            case _:
                totals["setup"] += size
    return totals


def fmt_size(b: int) -> str:
    """Format byte size using rich's built-in decimal formatter."""
    return f"{fmt_decimal(b):>10}"


def fmt_pct(b: int, tot: int) -> str:
    pct = (b / tot) * 100
    if pct < 0.1 and b > 0:
        return "[ <0.1% ]"
    return f"[{pct:5.1f}% ]"


@app.command()
def main(
    image_name: Annotated[str, typer.Argument(help="Image repository name")],
    tag: Annotated[str, typer.Argument(help="Image tag")],
    archive_path: Annotated[str, typer.Argument(help="Path to exported OCI archive")],
) -> None:
    image_ref = f"{image_name}:{tag}"
    archive_file = Path(archive_path)
    sig_file = Path(f"{archive_path}.asc")

    history_data = get_history_data(image_ref)
    if not history_data:
        console.print(
            f"[bold red]Error:[/] Could not inspect image [yellow]{image_ref}[/]. "
            "Run '[bold cyan]./scripts/image.sh build[/]' first."
        )
        raise typer.Exit(code=1)

    sig_info = inspect_gpg_signature(sig_file, archive_file)
    img_id = history_data[0].get("id", "N/A")
    created_at = history_data[0].get("Created", "N/A")

    totals = categorize_layers(history_data)
    total_size = sum(item.get("size", 0) for item in history_data) or 1

    console.print(
        Panel.fit(
            f"[bold green]Image ID:[/] [white]{img_id}[/]\n[bold green]Created At:[/] [white]{created_at}[/]",
            title=f"[bold cyan]IMAGE SIZE DIAGNOSTICS: {image_ref}[/]",
            border_style="blue",
        )
    )

    table = Table(
        title="Component Breakdown (Uncompressed Image)",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Component", style="cyan")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Percentage", justify="right", style="yellow")

    table.add_row(
        "1. Base Image (python slim)",
        fmt_size(totals["base"]),
        fmt_pct(totals["base"], total_size),
    )
    table.add_row(
        "2. Dependencies (/app/.venv)",
        fmt_size(totals["venv"]),
        fmt_pct(totals["venv"], total_size),
    )
    table.add_row(
        "3. App Code (/app/app-packages)",
        fmt_size(totals["app"]),
        fmt_pct(totals["app"], total_size),
    )
    table.add_row(
        "4. Setup & Metadata",
        fmt_size(totals["setup"]),
        fmt_pct(totals["setup"], total_size),
    )

    console.print(table)
    console.print(
        f"[bold]Total Uncompressed Image Size:[/] [green]{fmt_size(total_size)}[/] ({total_size:,} bytes)\n"
    )

    if archive_file.exists():
        arch_size = archive_file.stat().st_size
        ratio = (arch_size / total_size) * 100
        savings_mb = (total_size - arch_size) / (1024 * 1024)
        factor = total_size / arch_size if arch_size > 0 else 0
        console.print("[bold underline]--- Compressed Export Archive ---[/]")
        console.print(f"Archive Path:       [cyan]{archive_file}[/]")
        console.print(
            f"Archive Size:       [green]{fmt_size(arch_size)}[/] ({arch_size:,} bytes)"
        )
        console.print(
            f"Compression Ratio:  [yellow]{ratio:.1f}%[/] of original size ({factor:.2f}x compression)\n"
        )

        console.print("[bold underline]--- Signature Status (GPG) ---[/]")
        console.print(f"Signature File:     [cyan]{sig_file}[/]")

        match sig_info:
            case {"status": "VALID SIGNATURE", "signer": signer, "fingerprint": fp}:
                console.print("Status:             [green]VALID SIGNATURE[/]")
                console.print(f"Signer:             [white]{signer}[/]")
                console.print(f"Key Fingerprint:    [white]{fp}[/]")
            case {"status": status}:
                console.print(f"Status:             [red]{status}[/]")

        console.print("\n[bold underline]--- Insights ---[/]")
        console.print(
            f"* Base image accounts for [yellow]{(totals['base'] / total_size) * 100:.1f}%[/] of total image footprint."
        )
        console.print(
            f"* Python dependencies (.venv) account for [yellow]{(totals['venv'] / total_size) * 100:.1f}%[/] of image size."
        )
        console.print(
            f"* Compressed zstd archive saves [green]{savings_mb:.2f} MB[/] compared to container storage."
        )
        match sig_info:
            case {"status": "VALID SIGNATURE", "fingerprint": fp}:
                console.print(
                    f"* Archive is cryptographically signed with GPG key [white]{fp[:16]}[/]."
                )
            case _:
                console.print(
                    "* Archive is unsigned. Run [cyan]'./scripts/image.sh sign <KEY_ID>'[/] to generate GPG signature."
                )
    else:
        console.print(
            f"Archive Path:       [cyan]{archive_file}[/] [dim](Not exported yet)[/]"
        )


if __name__ == "__main__":
    app()
