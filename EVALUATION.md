# ChimeraVox — Evaluation

**Date:** 2026-10-02  
**Version evaluated:** 0.1.2  
**Author / Owner:** Mourad Soltani (@Mourad-Soltani)

## Overall Assessment

**Status: CI-ready and development-ready. Live ZeroGPU path is experimental.**

ChimeraVox has a clean stage-based architecture, a working offline path (`--dry-run` + MockProvider), automatic Ken Burns static-image fallback when all AI providers fail, a user-overridable `spaces.toml`, and a concrete failure runbook. The foundation is real.

The live image-to-video path remains bound by free-tier supply constraints (quotas, queues, Space churn). That is a category ceiling, not a ChimeraVox-specific defect.

### Strengths

| Area | Rating | Notes |
|------|--------|-------|
| Architecture | ★★★★★ | Linear pipeline, replaceable stages, clear errors |
| Offline / CI path | ★★★★★ | `--dry-run`, MockProvider, GitHub Actions matrix |
| Resilience floor | ★★★★☆ | Automatic Ken Burns fallback + RUNBOOK.md |
| Space override | ★★★★☆ | `spaces.toml` — no code release needed for renames |
| CLI / UX | ★★★★☆ | Typer + Rich, health, voices, dry-run |
| Free-tier honesty | ★★★★★ | README, EVALUATION, RUNBOOK are transparent |

### Weaknesses / Risks

| Risk | Severity | Notes |
|------|----------|-------|
| ZeroGPU quota / queue | High | Supply-side; mitigated by token + fallback chain + Ken Burns floor |
| Space rename / deprecation | Medium | Mitigated by `spaces.toml` + RUNBOOK |
| Gradio API signature drift | Medium | Providers probe multiple endpoints; still brittle |
| Live path not E2E-tested in CI | Medium | By design (CI is offline-only) |
| edge-tts install in restricted envs | Low | Lazy import; health warns rather than hard-fails |

### Known failure modes (actionable)

1. **Space renamed/deleted** → edit `spaces.toml` or drop the provider from `--providers`. See RUNBOOK Scenario 1.
2. **Quota exhausted** → set `HF_TOKEN`, wait, or let Ken Burns floor take over. See RUNBOOK Scenario 2.
3. **All AI providers down** → automatic Ken Burns pan/zoom over the photo + TTS. User still gets a video. See RUNBOOK Scenario 3.
4. **FFmpeg / edge-tts missing** → install system/package deps. Health check reports it.

### Readiness matrix

| Path | Status |
|------|--------|
| Offline dry-run / unit tests / CI | Ready |
| Local development against mock + Ken Burns | Ready |
| Personal use with HF token + patience | Experimental |
| Unattended / high-volume / production SLA | Not ready |

### Framing note

Earlier language of “production-ready for the offline/mock path” was slightly oversold. More precise: the offline path is **CI-ready and development-ready**. The real path a user cares about (live ZeroGPU generation) has not been exercised end-to-end on a clean machine in CI. That is acceptable at this stage; it is not the same as production-ready.

### Recommended next (then stop)

1. ~~Failure runbook~~ → done (`docs/RUNBOOK.md`)
2. ~~Static-image floor~~ → done (Ken Burns auto-fallback)
3. ~~Space override without code release~~ → done (`spaces.toml`)
4. Do **not** add paid-provider fallbacks until the free-tier edges above are proven stable in real use.

### Conclusion

v0.1.2 is a credible free-tier photo-to-video foundation with an honest resilience floor. The remaining risk is external (Space availability and quotas). The code does what is reasonable to tolerate that reality.
