"""Main ChimeraVox pipeline orchestration."""

from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path

from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from chimera_vox.config import Config
from chimera_vox.errors import HealthCheckError
from chimera_vox.health import run_health_checks
from chimera_vox.providers.registry import build_provider_chain
from chimera_vox.stages.clip_generator import generate_clips
from chimera_vox.stages.script_parser import full_text, parse_script
from chimera_vox.stages.stitcher import stitch_clips
from chimera_vox.stages.tts import generate_narration
from chimera_vox.stages.upscaler import upscale_video
from chimera_vox.utils.files import ensure_dir
from chimera_vox.utils.logging import get_console

log = logging.getLogger(__name__)
console = get_console()


async def run_pipeline(config: Config) -> Path:
    """Execute the full pipeline and return the output path."""
    start = time.time()
    config.validate()

    ensure_dir(config.temp_dir)
    ensure_dir(config.cache_dir)

    if config.dry_run:
        log.info("Dry-run mode: using mock provider only")
        providers = build_provider_chain(["mock"], hf_token=None)
    else:
        providers = build_provider_chain(config.providers, hf_token=config.hf_token)

    # Health checks
    if not config.skip_health_check:
        console.print("[bold]Running health checks…[/]")
        report = await run_health_checks(config, providers)
        console.print(report.summary())
        if not report.ok:
            raise HealthCheckError(
                "One or more critical health checks failed. "
                "Use --no-health-check to skip (not recommended)."
            )

    # Parse script
    segments = parse_script(config.script_text, clip_duration=config.clip_duration)
    if not segments:
        raise ValueError("Script produced no segments")
    log.info("Parsed %d segments", len(segments))

    narration_text = full_text(segments)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # TTS
        tts_task = progress.add_task("Generating narration (edge-tts)…", total=None)
        audio_path = config.temp_dir / "narration.mp3"
        await generate_narration(
            narration_text, audio_path, voice=config.voice
        )
        progress.update(tts_task, completed=1)

        # Clips
        clip_task = progress.add_task(
            f"Generating {len(segments)} AI clips…", total=None
        )
        clips = await generate_clips(
            providers=providers,
            photo=config.photo,
            segments=segments,
            prompt=config.prompt,
            temp_dir=config.temp_dir,
            clip_duration=config.clip_duration,
        )
        progress.update(clip_task, completed=1)

        # Stitch
        stitch_task = progress.add_task("Stitching clips + audio…", total=None)
        stitched = config.temp_dir / "stitched.mp4"
        stitch_clips(
            clips=clips,
            audio_path=audio_path,
            output_path=stitched,
            temp_dir=config.temp_dir,
            fps=config.fps,
            threads=config.threads or 4,
        )
        progress.update(stitch_task, completed=1)

        # Upscale (always normalize to target resolution + aspect pad)
        final = config.output
        up_task = progress.add_task(
            f"Encoding / upscaling to {config.resolution}…", total=None
        )
        upscale_video(
            input_path=stitched,
            output_path=final,
            resolution=config.resolution,
            temp_dir=config.temp_dir,
            fps=config.fps,
            threads=config.threads or 4,
        )
        progress.update(up_task, completed=1)

    elapsed = time.time() - start
    console.print(
        f"[bold green]Done[/] → {final}  ({elapsed:.1f}s, {len(segments)} clips)"
    )
    return final


def run_pipeline_sync(config: Config) -> Path:
    """Synchronous entry point."""
    return asyncio.run(run_pipeline(config))
