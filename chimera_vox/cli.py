"""ChimeraVox command-line interface."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

from chimera_vox import __version__
from chimera_vox.config import Config
from chimera_vox.constants import (
    DEFAULT_CLIP_DURATION,
    DEFAULT_FPS,
    DEFAULT_PROVIDERS,
    DEFAULT_RESOLUTION,
    DEFAULT_VOICE,
    RESOLUTIONS,
)
from chimera_vox.pipeline import run_pipeline_sync
from chimera_vox.providers.registry import available_provider_names
from chimera_vox.utils.logging import get_console, setup_logging

app = typer.Typer(
    name="chimera-vox",
    help="Forge videos from a single photo and a script — free-tier pipeline.",
    add_completion=False,
    no_args_is_help=True,
)
console = get_console()


def _version_callback(value: bool) -> None:
    if value:
        console.print(f"chimera-vox {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """ChimeraVox — free-tier photo + script → video."""


@app.command()
def run(
    photo: Path = typer.Option(
        ...,
        "--photo",
        "-p",
        exists=True,
        dir_okay=False,
        help="Input photo (JPEG/PNG).",
    ),
    script: Path = typer.Option(
        ...,
        "--script",
        "-s",
        exists=True,
        dir_okay=False,
        help="Script file (.txt/.md).",
    ),
    prompt: str = typer.Option(
        "",
        "--prompt",
        "-P",
        help="Additional visual prompt for the AI model.",
    ),
    resolution: str = typer.Option(
        DEFAULT_RESOLUTION,
        "--resolution",
        "-r",
        help=f"Output resolution: {', '.join(RESOLUTIONS)}",
    ),
    output: Path = typer.Option(
        Path("output.mp4"),
        "--output",
        "-o",
        help="Output video path.",
    ),
    voice: str = typer.Option(
        DEFAULT_VOICE,
        "--voice",
        help="edge-tts voice name.",
    ),
    fps: int = typer.Option(DEFAULT_FPS, "--fps", help="Frame rate."),
    clip_duration: float = typer.Option(
        DEFAULT_CLIP_DURATION,
        "--clip-duration",
        help="Target seconds per AI clip (1-10).",
    ),
    providers: str = typer.Option(
        ",".join(DEFAULT_PROVIDERS),
        "--providers",
        help=f"Comma-separated provider order. Available: {', '.join(available_provider_names())}",
    ),
    threads: Optional[int] = typer.Option(
        None, "--threads", help="FFmpeg threads (default: all cores)."
    ),
    skip_health_check: bool = typer.Option(
        False,
        "--no-health-check",
        help="Skip pre-flight checks (not recommended).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Use mock provider only (no network / ZeroGPU calls). Great for testing the pipeline.",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Debug logging."
    ),
) -> None:
    """Generate a video from a photo + script."""
    setup_logging(verbose)

    script_text = script.read_text(encoding="utf-8")
    provider_list = [p.strip() for p in providers.split(",") if p.strip()]

    cfg = Config(
        photo=photo,
        script_text=script_text,
        prompt=prompt,
        resolution=resolution,
        output=output,
        voice=voice,
        fps=fps,
        clip_duration=clip_duration,
        providers=provider_list,
        threads=threads,
        skip_health_check=skip_health_check,
        dry_run=dry_run,
        verbose=verbose,
    )

    try:
        run_pipeline_sync(cfg)
    except Exception as exc:
        console.print(f"[bold red]Error:[/] {exc}")
        raise typer.Exit(code=1) from exc


@app.command()
def health(
    photo: Optional[Path] = typer.Option(
        None, "--photo", exists=True, dir_okay=False
    ),
    providers: str = typer.Option(
        ",".join(DEFAULT_PROVIDERS),
        "--providers",
        help="Providers to check.",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Run health checks and exit."""
    setup_logging(verbose)
    from chimera_vox.health import run_health_checks
    from chimera_vox.providers.registry import build_provider_chain

    provider_list = [p.strip() for p in providers.split(",") if p.strip()]
    chain = build_provider_chain(provider_list)

    # Minimal config for checks that need it
    if photo is None:
        # create a tiny dummy
        from PIL import Image
        import tempfile
        tmp = Path(tempfile.mkdtemp()) / "dummy.png"
        Image.new("RGB", (64, 64), color="blue").save(tmp)
        photo = tmp

    cfg = Config(
        photo=photo,
        script_text="Health check.",
        providers=provider_list,
        temp_dir=Path(".chimera_tmp"),
    )

    report = asyncio.run(run_health_checks(cfg, chain))
    console.print(report.summary())
    if not report.ok:
        raise typer.Exit(code=1)


@app.command()
def voices(
    language: Optional[str] = typer.Option(
        None,
        "--language",
        "-l",
        help="Filter by language prefix (e.g. en-US).",
    ),
) -> None:
    """List available edge-tts voices."""
    setup_logging(False)
    import edge_tts

    async def _list() -> None:
        all_voices = await edge_tts.list_voices()
        table = Table(title="edge-tts Voices")
        table.add_column("ShortName", style="cyan")
        table.add_column("Gender")
        table.add_column("Locale")

        for v in sorted(all_voices, key=lambda x: x["ShortName"]):
            if language and not v["Locale"].lower().startswith(language.lower()):
                continue
            table.add_row(v["ShortName"], v.get("Gender", ""), v["Locale"])

        console.print(table)

    asyncio.run(_list())


if __name__ == "__main__":
    app()
