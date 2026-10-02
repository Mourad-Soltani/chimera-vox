"""Configuration handling for ChimeraVox."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from chimera_vox.constants import (
    DEFAULT_CLIP_DURATION,
    DEFAULT_FPS,
    DEFAULT_PROVIDERS,
    DEFAULT_RESOLUTION,
    DEFAULT_VOICE,
    RESOLUTIONS,
)
from chimera_vox.errors import ConfigError


@dataclass
class Config:
    """Runtime configuration for a ChimeraVox run."""

    photo: Path
    script_text: str
    prompt: str = ""
    resolution: str = DEFAULT_RESOLUTION
    output: Path = field(default_factory=lambda: Path("output.mp4"))
    voice: str = DEFAULT_VOICE
    fps: int = DEFAULT_FPS
    clip_duration: float = DEFAULT_CLIP_DURATION
    providers: list[str] = field(default_factory=lambda: list(DEFAULT_PROVIDERS))
    threads: int | None = None
    skip_health_check: bool = False
    verbose: bool = False
    hf_token: str | None = None
    temp_dir: Path = field(default_factory=lambda: Path(".chimera_tmp"))
    cache_dir: Path = field(default_factory=lambda: Path(".chimera_cache"))

    def __post_init__(self) -> None:
        self.photo = Path(self.photo).resolve()
        self.output = Path(self.output)
        self.temp_dir = Path(self.temp_dir)
        self.cache_dir = Path(self.cache_dir)

        if self.hf_token is None:
            self.hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")

        # Allow short voice names
        from chimera_vox.constants import VOICES
        if self.voice in VOICES:
            self.voice = VOICES[self.voice]

        if self.threads is None:
            self.threads = os.cpu_count() or 4

    def validate(self) -> None:
        """Raise ConfigError if the configuration is invalid."""
        if not self.photo.exists():
            raise ConfigError(f"Photo not found: {self.photo}")
        if self.photo.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise ConfigError(f"Unsupported photo format: {self.photo.suffix}")
        if not self.script_text.strip():
            raise ConfigError("Script text is empty")
        if self.resolution not in RESOLUTIONS:
            raise ConfigError(
                f"Unknown resolution '{self.resolution}'. "
                f"Options: {', '.join(RESOLUTIONS)}"
            )
        if not (1.0 <= self.clip_duration <= 10.0):
            raise ConfigError("clip_duration must be between 1.0 and 10.0 seconds")
        if self.fps < 1 or self.fps > 60:
            raise ConfigError("fps must be between 1 and 60")
        if not self.providers:
            raise ConfigError("At least one provider must be specified")

    @property
    def target_size(self) -> tuple[int, int]:
        """Return (width, height) for the requested resolution."""
        return RESOLUTIONS[self.resolution]
