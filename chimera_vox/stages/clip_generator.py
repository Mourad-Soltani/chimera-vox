"""Generate AI video clips for each script segment, with provider fallback."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from chimera_vox.errors import AllProvidersFailedError
from chimera_vox.providers.base import Provider, ProviderResult
from chimera_vox.stages.script_parser import ScriptSegment
from chimera_vox.utils.ffmpeg import extract_last_frame
from chimera_vox.utils.files import ensure_dir

log = logging.getLogger(__name__)


async def generate_clips(
    providers: Sequence[Provider],
    photo: Path,
    segments: Sequence[ScriptSegment],
    prompt: str,
    temp_dir: Path,
    clip_duration: float,
) -> list[ProviderResult]:
    """
    Generate one clip per segment. Uses last-frame continuity so the subject
    evolves naturally from clip to clip.

    If every provider in the chain fails, automatically falls back to the
    Ken Burns static-image provider so the user still gets a narrated video.
    """
    ensure_dir(temp_dir)
    clips: list[ProviderResult] = []
    current_image = photo

    for seg in segments:
        composed = _compose_prompt(prompt, seg.text)
        log.info(
            "Generating clip %d/%d (provider chain, ~%.1fs) …",
            seg.index + 1,
            len(segments),
            seg.estimated_duration,
        )
        result = await _generate_with_fallback(
            providers,
            current_image,
            composed,
            min(clip_duration, seg.estimated_duration + 0.5),
        )
        clips.append(result)

        # Continuity: next clip starts from the last frame of this one
        next_frame = temp_dir / f"frame_{seg.index:03d}.png"
        try:
            extract_last_frame(result.path, next_frame)
            current_image = next_frame
        except Exception as exc:  # noqa: BLE001
            log.warning("Could not extract last frame for continuity: %s", exc)
            # keep previous image

    return clips


async def _generate_with_fallback(
    providers: Sequence[Provider],
    image: Path,
    prompt: str,
    duration: float,
) -> ProviderResult:
    last_error: Exception | None = None
    tried_names: list[str] = []

    for provider in providers:
        tried_names.append(provider.name)
        try:
            log.debug("Trying provider: %s", provider.name)
            return await provider.generate_clip(image, prompt, duration)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            log.warning("Provider %s failed: %s", provider.name, exc)
            continue

    # Automatic static-image floor: Ken Burns if not already tried
    if "kenburns" not in tried_names and "mock" not in tried_names:
        log.warning(
            "All AI providers failed — falling back to Ken Burns static floor"
        )
        try:
            from chimera_vox.providers.kenburns import KenBurnsProvider

            kb = KenBurnsProvider()
            return await kb.generate_clip(image, prompt, duration)
        except Exception as kb_exc:  # noqa: BLE001
            last_error = kb_exc
            log.error("Ken Burns fallback also failed: %s", kb_exc)

    raise AllProvidersFailedError(
        f"All providers failed (tried: {', '.join(tried_names)}). "
        f"Last error: {last_error}. "
        "See docs/RUNBOOK.md for recovery steps."
    )


def _compose_prompt(base_prompt: str, segment_text: str) -> str:
    """Merge the user's visual prompt with the segment's narration context."""
    base = base_prompt.strip()
    snippet = segment_text.strip()
    if len(snippet) > 220:
        snippet = snippet[:220] + "..."
    if base:
        return f"{base}. Scene context: {snippet}"
    return snippet
