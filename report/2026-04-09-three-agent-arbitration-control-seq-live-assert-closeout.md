# 2026-04-09 three-agent arbitration control-seq live-assert closeout

## why
- smoke-only runtime harness tightening

## changed file
- `.pipeline/smoke-three-agent-arbitration.sh`

## verification actually run
- `bash -n .pipeline/smoke-three-agent-arbitration.sh`
- `PIPELINE_SMOKE_KEEP_SESSION_ON_FAILURE=0 PIPELINE_SMOKE_KEEP_SESSION_ON_SUCCESS=0 ./.pipeline/smoke-three-agent-arbitration.sh`
- `git diff --check`

## residual
- smoke-local prompt is intentionally narrower than runtime prompt
- runtime contract itself was not changed
