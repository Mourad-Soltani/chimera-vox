"""Text-to-speech generation via edge-tts."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from chimera_vox.errors import TTSGenerationError

log = logging.getLogger(__name__)


async def generate_narration(
    text: str,
    output_path: Path,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
) -> Path:
    """Generate narration audio for text and save to output_path."""
    try:
        import edge_tts
    except ImportError as exc:
        raise TTSGenerationError("edge-tts is not installed") from exc

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(str(output_path))
    except Exception as exc:  # noqa: BLE001
        raise TTSGenerationError(f"edge-tts failed: {exc}") from exc

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise TTSGenerationError("TTS produced empty or missing file")

    log.info("Narration written to %s (%.1f KB)", output_path, output_path.stat().st_size / 1024)
    return output_path


def generate_narration_sync(
    text: str,
    output_path: Path,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
) -> Path:
    """Synchronous wrapper around generate_narration."""
    return asyncio.run(generate_narration(text, output_path, voice, rate))


async def list_voices() -> list[dict]:
    """Return the list of available edge-tts voices."""
    import edge_tts

    return await edge_tts.list_voices()
