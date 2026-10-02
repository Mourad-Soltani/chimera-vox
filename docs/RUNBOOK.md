# ChimeraVox Failure Runbook

When the live path fails, use this guide. The offline path (`--dry-run`) is unaffected by any of these issues.

## Quick diagnosis

```bash
chimera-vox health --verbose
```

Look at the `provider:*` lines:
- **pass** → Space is reachable (HTTP)
- **warn** → timeout, 4xx/5xx, or network error
- Missing entirely → provider not in your chain

Also check:
```bash
echo $HF_TOKEN          # should be set for higher quota
df -h .                 # need ≥ 5 GB free
ffmpeg -version         # must be present
```

---

## Scenario 1 — Space renamed or deleted

**Symptoms:** `provider:ltx` (or cogvideox / wan) shows warn / fail; generation raises `ProviderError` or eventually `AllProvidersFailedError`.

**Fix (no code release needed):**

1. Find a working replacement Space on Hugging Face (search “LTX”, “CogVideoX”, “Wan Animate”, “image to video”).
2. Edit `spaces.toml` in the project root (create it if missing):

```toml
[spaces]
ltx = "new-user/new-ltx-space"
cogvideox = "new-user/new-cogvideox-space"
wan = "new-user/new-wan-space"
```

3. Re-run. The registry loads `spaces.toml` over the built-in defaults.

Alternatively, temporarily drop the broken provider:

```bash
chimera-vox run ... --providers cogvideox,wan,kenburns
```

---

## Scenario 2 — Quota exhausted / queue too long

**Symptoms:** Provider is reachable but `predict` times out or returns rate-limit / queue errors after retries.

**Fix:**

1. Set a Hugging Face token (raises ZeroGPU quota):

```bash
export HF_TOKEN="hf_..."
# or put it in .env
```

2. Wait and retry later (quotas reset on a rolling window; peak hours are worst).
3. Shorten the script or raise `--clip-duration` so fewer clips are requested.
4. Fall back to the static floor:

```bash
chimera-vox run ... --providers kenburns
# or just let the automatic Ken Burns fallback trigger after all AI providers fail
```

---

## Scenario 3 — All AI providers down

**Symptoms:** `AllProvidersFailedError` (or the pipeline silently continues with Ken Burns if the automatic fallback is active).

**What happens automatically (v0.1.2+):**  
If every AI provider in the chain fails, ChimeraVox falls back to a **Ken Burns** pan/zoom over the original photo, still muxed with the TTS narration. You get a video — not the AI-animated one you wanted, but a complete narrated video.

**Manual options:**

```bash
# Force static floor only
chimera-vox run ... --providers kenburns

# Offline test of the whole pipeline
chimera-vox run ... --dry-run
```

---

## Scenario 4 — edge-tts / FFmpeg missing

**Symptoms:** Health check shows fail/warn for `edge-tts` or `ffmpeg`.

```bash
pip install edge-tts
# and install ffmpeg via your OS package manager
sudo apt install ffmpeg   # Debian/Ubuntu
brew install ffmpeg       # macOS
```

---

## Getting help

1. Run `chimera-vox health --verbose` and save the output.
2. Check the Space pages on huggingface.co for status / discussions.
3. Open an issue with the health output and the exact command you ran.
