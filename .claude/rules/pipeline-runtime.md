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
- If a `needs_operator` slot only presents labeled choices, such as lettered, numbered, inline parenthesized, or Korean `n안` options, that current docs, milestones, and latest `work/` + `verify/` can resolve, send it through advisory-first triage before waiting on the operator. Keep safety, destructive, auth/credential, approval-record, and truth-sync blockers in the decision header as real stops.
- If watcher prompts you for operator retriage, write one newer control slot. An idle return with no next control is treated as `operator_retriage_no_next_control` and watcher may escalate the same gated request to Gemini.
- Treat stale redispatch seriously: if the same `HANDOFF_SHA` is already closed by the latest persistent notes, report `BLOCK_REASON_CODE: already_implemented`.
- Do not hardcode current branch names, commit SHAs, `CONTROL_SEQ` values, pane ids, Korean display labels, exact operator prose, or one-off control-file bodies in runtime logic. Use structured metadata, shared parsers, schema helpers, status-label helpers, and fixtures.
- Do not duplicate near-copy watcher/supervisor/launcher/controller truth logic. Move shared truth to the owning module or `pipeline_runtime/*` helper and keep clients thin.
- Do not keep adding unrelated branches to a large function or file. Extract parsing, labeling, control writing, lane-surface, or event-contract responsibilities when concentration makes the next fix harder.
- For runtime / launcher work, prefer focused incident replay and live stability checks over rerunning long soak by default.
- Only reopen broad soak expectations when supervisor / watcher / tmux adapter / wrapper-event contracts changed, state-writer contracts changed, or an adoption-final gate is explicitly required.
- When stop / degraded / dispatch incidents change, keep the surface truthful in runtime status, launcher recent log, and controller-visible state; do not hide a repeated stall behind generic READY / WORKING copy.
