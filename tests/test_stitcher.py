from pathlib import Path

import pytest

from chimera_vox.errors import StitchingError
from chimera_vox.providers.base import ProviderResult
from chimera_vox.stages.stitcher import stitch_clips
from chimera_vox.utils.ffmpeg import ffmpeg_available

pytestmark = pytest.mark.skipif(
    not ffmpeg_available(), reason="ffmpeg not available"
)


def _make_clip(path: Path, colour: str = "red", duration: float = 1.0) -> Path:
    import subprocess

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=c={colour}:s=320x240:d={duration}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ],
        check=True,
    )
    return path


def test_stitch_empty_raises(tmp_path):
    with pytest.raises(StitchingError):
        stitch_clips([], tmp_path / "a.mp3", tmp_path / "out.mp4", tmp_path)


def test_stitch_two_clips(tmp_path):
    c1 = _make_clip(tmp_path / "c1.mp4", "red")
    c2 = _make_clip(tmp_path / "c2.mp4", "blue")
    clips = [
        ProviderResult(c1, 1.0, "test"),
        ProviderResult(c2, 1.0, "test"),
    ]
    # Create a silent audio so mux path is exercised
    import subprocess

    audio = tmp_path / "silence.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=44100:cl=mono",
            "-t",
            "2",
            "-q:a",
            "9",
            "-acodec",
            "libmp3lame",
            str(audio),
        ],
        check=True,
    )
    out = stitch_clips(clips, audio, tmp_path / "out.mp4", tmp_path)
    assert out.exists()
    assert out.stat().st_size > 0
