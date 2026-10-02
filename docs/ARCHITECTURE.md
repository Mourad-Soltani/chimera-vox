# ChimeraVox Architecture

## Overview

ChimeraVox is a linear, stage-based pipeline. Each stage is independently
testable and replaceable.

```
Config → Health → ScriptParser → TTS → ClipGenerator → Stitcher → Upscaler → Output
```

## Stages

1. **Config** (`config.py`)
   Validates inputs, resolves environment overrides, and exposes `target_size`.

2. **Health** (`health.py`)
   Runs synchronous and asynchronous checks:
   - FFmpeg / ffprobe availability
   - edge-tts importability
   - Disk space (>= 5 GB free)
   - Photo readability via Pillow
   - Provider Space reachability via HTTP HEAD

   `run_health_checks` is async and must be awaited from an event loop. The CLI
   wraps it in `asyncio.run()`; the pipeline awaits it directly.

   Failures block the pipeline; warnings (e.g. unreachable provider) are logged.

3. **ScriptParser** (`stages/script_parser.py`)
   Splits the script by paragraphs and sentences, then merges into segments whose
   estimated spoken duration is close to `clip_duration`. Uses 2.5 words/second as
   the narration pace estimate.

4. **TTS** (`stages/tts.py`)
   Uses edge-tts (free, no API key) to generate a single MP3 narration track for
   the full script.

5. **ClipGenerator** (`stages/clip_generator.py`)
   For each segment:
   1. Compose a prompt from the user's visual prompt + segment narration context.
   2. Try each provider in order until one succeeds.
   3. Extract the last frame of the generated clip.
   4. Use that frame as the input image for the next clip (continuity).

6. **Stitcher** (`stages/stitcher.py`)
   Uses FFmpeg's concat demuxer to join clips, then muxes the narration audio.

7. **Upscaler** (`stages/upscaler.py`)
   Rescales the stitched video to the target resolution using the lanczos
   filter, preserving aspect ratio with black padding if needed.

## Providers

| Name       | Space                      | Notes                          |
|------------|----------------------------|--------------------------------|
| ltx        | rahul7star/LTX-2.3-turbo   | 22B DiT, video+audio, 2-5s     |
| cogvideox  | THUDM/CogVideoX-5B         | 5B, ~6s clips, 720p            |
| wan        | Wan-AI/Wan-Animate         | Character animation, ~2s clips |

All providers use `gradio_client`. The registry probes a list of common API
endpoint names (`/generate`, `/predict`, `/infer`, …) until one works.

## Error Handling

- Each provider call is wrapped in `retry_async` with exponential backoff.
- If a provider exhausts retries, the next provider in the chain is tried.
- If all providers fail, `AllProvidersFailedError` is raised.

## Performance Notes

- FFmpeg encoding uses `-threads N` (defaults to all CPU cores).
- Audio is encoded once (AAC 192 kbps) during the mux step.
- For 8K output, expect 10-30 minutes of CPU encoding on a modern laptop.

## Free-Tier Constraints

- ZeroGPU Spaces have daily quotas and shared queues.
- Native generation is typically 720p–1080p; 4K/8K is achieved via FFmpeg upscaling.
- Each Space has its own VRAM and time limits (typically 3–6 seconds per clip).
