"""Project-wide constants."""

from __future__ import annotations

from pathlib import Path
from typing import Final

# Resolution presets: (width, height)
RESOLUTIONS: Final[dict[str, tuple[int, int]]] = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "4k": (3840, 2160),
    "8k": (7680, 4320),
}

DEFAULT_RESOLUTION: Final[str] = "1080p"
DEFAULT_FPS: Final[int] = 24
DEFAULT_CLIP_DURATION: Final[float] = 3.0
DEFAULT_VOICE: Final[str] = "en-US-AriaNeural"

# Provider order (first available wins). kenburns is the automatic last-resort floor.
DEFAULT_PROVIDERS: Final[list[str]] = ["ltx", "cogvideox", "wan"]

# Built-in Hugging Face ZeroGPU Spaces (overridable via spaces.toml)
_DEFAULT_SPACES: dict[str, str] = {
    "ltx": "rahul7star/LTX-2.3-turbo",
    "cogvideox": "THUDM/CogVideoX-5B",
    "wan": "Wan-AI/Wan-Animate",
}


def _load_spaces() -> dict[str, str]:
    """Load Space IDs, preferring spaces.toml in cwd or package root if present."""
    spaces = dict(_DEFAULT_SPACES)
    candidates = [
        Path.cwd() / "spaces.toml",
        Path(__file__).resolve().parent.parent / "spaces.toml",
    ]
    for path in candidates:
        if not path.is_file():
            continue
        try:
            # Minimal TOML subset parser for [spaces] key = "value"
            section = False
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("["):
                    section = line.strip("[]").strip().lower() == "spaces"
                    continue
                if section and "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip().lower()
                    val = val.strip().strip('"').strip("'")
                    if key and val:
                        spaces[key] = val
            break  # first file found wins
        except Exception:
            continue
    return spaces


SPACES: Final[dict[str, str]] = _load_spaces()

# Common Gradio API endpoint names to probe
API_CANDIDATES: Final[list[str]] = [
    "/generate",
    "/predict",
    "/infer",
    "/generate_video",
    "/animate",
    "/run/predict",
]

# Retry defaults
MAX_RETRIES: Final[int] = 3
RETRY_BASE_DELAY: Final[float] = 2.0
RETRY_MAX_DELAY: Final[float] = 60.0

# Disk space warning threshold (GB)
MIN_DISK_GB: Final[float] = 5.0

# Curated edge-tts voices (short name -> full name)
VOICES: Final[dict[str, str]] = {
    "aria": "en-US-AriaNeural",
    "jenny": "en-US-JennyNeural",
    "guy": "en-US-GuyNeural",
    "andrew": "en-US-AndrewMultilingualNeural",
    "emma": "en-US-EmmaMultilingualNeural",
    "sonia": "en-GB-SoniaNeural",
    "ryan": "en-GB-RyanNeural",
    "natasha": "en-AU-NatashaNeural",
    "neerja": "en-IN-NeerjaNeural",
    # French
    "denise": "fr-FR-DeniseNeural",
    "henri": "fr-FR-HenriNeural",
    # Arabic
    "hamed": "ar-SA-HamedNeural",       # Saudi male
    "zariyah": "ar-SA-ZariyahNeural",   # Saudi female
    "salma": "ar-EG-SalmaNeural",       # Egypt female
    "shakir": "ar-EG-ShakirNeural",     # Egypt male
    "fatima": "ar-AE-FatimaNeural",     # UAE female
    "hamdan": "ar-AE-HamdanNeural",     # UAE male
    "mouna": "ar-MA-MounaNeural",       # Morocco female
    "jamal": "ar-MA-JamalNeural",       # Morocco male
}

# Ordered list for CLI / Gradio / Streamlit dropdowns
VOICE_CHOICES: Final[list[str]] = [
    # English
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-GB-SoniaNeural",
    "en-GB-RyanNeural",
    # French
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    # Arabic
    "ar-SA-HamedNeural",
    "ar-SA-ZariyahNeural",
    "ar-EG-SalmaNeural",
    "ar-EG-ShakirNeural",
    "ar-AE-FatimaNeural",
    "ar-AE-HamdanNeural",
    "ar-MA-MounaNeural",
    "ar-MA-JamalNeural",
]
