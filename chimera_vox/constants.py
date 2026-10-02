"""Project-wide constants."""

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

# Provider order (first available wins)
DEFAULT_PROVIDERS: Final[list[str]] = ["ltx", "cogvideox", "wan"]

# Hugging Face ZeroGPU Spaces
SPACES: Final[dict[str, str]] = {
    "ltx": "rahul7star/LTX-2.3-turbo",
    "cogvideox": "THUDM/CogVideoX-5B",
    "wan": "Wan-AI/Wan-Animate",
}

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
}
