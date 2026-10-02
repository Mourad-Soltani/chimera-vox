# ChimeraVox

> Forge videos from a single photo and a script — entirely on free tiers.

**Author:** Mourad Soltani (@Mourad-Soltani)  
**Version:** 0.1.0

ChimeraVox turns a still photo plus a written script into a narrated, AI-animated
video at up to 8K resolution, using only free infrastructure:

- **Hugging Face ZeroGPU Spaces** for image-to-video generation (LTX-2.3 Turbo,
  CogVideoX-5B, Wan Animate)
- **Microsoft Edge Neural Voices** (via `edge-tts`) for narration — no API key
- **FFmpeg** for stitching, audio muxing, and resolution upscaling

## Quick Start

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Set your Hugging Face token (optional but recommended for higher quota)
export HF_TOKEN="hf_..."

# 3. Run
chimera-vox run \
  --photo ./my_photo.jpg \
  --script ./my_script.txt \
  --prompt "cinematic slow pan, warm golden hour light" \
  --resolution 4k \
  --output ./final_4k.mp4
```

## CLI Reference

```
chimera-vox run [OPTIONS]

  --photo PATH          Input photo (JPEG/PNG, ideally 4K+ source)
  --script PATH         Script file (.txt or .md)
  --prompt TEXT         Additional visual prompt for the AI model
  --resolution TEXT     Output resolution: 720p | 1080p | 4k | 8k  [default: 1080p]
  --voice TEXT          edge-tts voice name  [default: en-US-AriaNeural]
  --fps INTEGER         Frame rate  [default: 24]
  --clip-duration FLOAT Seconds per AI clip  [default: 3.0]
  --providers TEXT      Comma-separated provider order  [default: ltx,cogvideox,wan]
  --output PATH         Output video path  [default: output.mp4]
  --threads INTEGER     FFmpeg threads  [default: all cores]
  --no-health-check     Skip pre-flight checks (not recommended)
  --verbose             Debug logging

chimera-vox health       Run health checks and exit
chimera-vox voices       List available edge-tts voices
```

## Resolution Options

| Flag  | Width × Height | Notes                              |
|-------|----------------|------------------------------------|
| 720p  | 1280 × 720     | Fastest                            |
| 1080p | 1920 × 1080    | Recommended balance                |
| 4k    | 3840 × 2160    | AI upscale from base clip          |
| 8k    | 7680 × 4320    | Heavy; needs 32 GB+ RAM and disk   |

## How It Works

1. **Health check** — verifies FFmpeg, edge-tts, network, disk, and HF Space reachability.
2. **Script parsing** — splits the script into sentence-level chunks and estimates duration.
3. **TTS** — generates full narration audio via edge-tts (free, unlimited, no key).
4. **Clip generation** — for each chunk, sends the current frame + prompt to a ZeroGPU Space.
   Uses last-frame continuity so the video flows naturally between clips.
5. **Stitching** — FFmpeg concat demuxer joins clips; narration is muxed in.
6. **Upscaling** — FFmpeg lanczos rescales to the requested resolution.

## Free-Tier Limits (Honest)

- ZeroGPU Spaces have daily quotas and shared queues. Expect waits during peak hours.
- Native AI generation is typically 720p–1080p. 4K/8K is achieved via upscaling.
- Clips are 2–6 seconds each. Long scripts produce many clips; stitching is local and fast.
- No watermark is added by ChimeraVox.

## Development

```bash
make dev          # install with test deps
make test         # run pytest
make lint         # ruff check
make health       # run health checks
```

## License

MIT
