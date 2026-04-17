---
paths:
  - ".pipeline/**/*.md"
  - "watcher_core.py"
  - "pipeline_runtime/**/*.py"
  - "pipeline-launcher.py"
  - "controller/**/*.py"
  - "controller/**/*.html"
  - "scripts/pipeline_runtime_gate.py"
---

# Pipeline Runtime Rules

- Persistent truth lives in `work/` and `verify/`; `.pipeline/` files are rolling control slots.
- Claude executes only `.pipeline/claude_handoff.md` when it is the newest valid control with `STATUS: implement`.
- Do not answer `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, or `.pipeline/gemini_advice.md` as if they were Claude execution slots.
- If the assigned handoff is blocked, stale, already implemented, or contradicted by the latest `work/` + `verify/`, emit the exact `implement_blocked` sentinel and stop rather than improvising a new slice.
- Treat stale redispatch seriously: if the same `HANDOFF_SHA` is already closed by the latest persistent notes, report `BLOCK_REASON_CODE: already_implemented`.
- For runtime / launcher work, prefer focused incident replay and live stability checks over rerunning long soak by default.
- Only reopen broad soak expectations when supervisor / watcher / tmux adapter / wrapper-event contracts changed, state-writer contracts changed, or an adoption-final gate is explicitly required.
- When stop / degraded / dispatch incidents change, keep the surface truthful in runtime status, launcher recent log, and controller-visible state; do not hide a repeated stall behind generic READY / WORKING copy.

