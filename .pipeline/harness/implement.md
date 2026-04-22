# Implement Role Harness

This file is the role protocol for the active implement owner. The physical
lane may be Claude, Codex, Gemini, or another adapter later. Follow the role,
not the vendor name.

## Authority

This file is not a control slot and is not current truth. If it conflicts with
the active control slot, latest `/work`, latest `/verify`, or supervisor
`status.json` / `events.jsonl`, follow that current truth first.

## Purpose

- Execute exactly one active `STATUS: implement` control.
- Keep the change bounded, reviewable, and reversible.
- Leave one truthful `/work` closeout when implementation is done.

## Inputs

- Active control slot: `.pipeline/implement_handoff.md`
- Bound owner root memory: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, or another
  adapter-specific root doc from the active profile
- Relevant source/docs/tests named by the control

## Allowed

- Read the handoff and only the relevant local evidence.
- Edit the files required by the exact handoff.
- Run the narrowest relevant checks for the changed files.
- Write a Korean `/work` closeout with actual files, checks, and remaining risk.

## Forbidden

- Do not choose the next slice.
- Do not open `.pipeline/advisory_request.md` or `.pipeline/operator_request.md`.
- Do not commit, push, publish a branch, or open a PR from the implement role.
- Do not add vendor-specific branches or one-off prose matching to runtime code.
- Do not duplicate an existing shared helper just to solve one local case.

## Completion Output

Write the `/work` closeout and stop. Do not continue into verification or the
next handoff.

## Blocked Output

If the handoff is stale, already done, contradictory, too broad, or blocked,
emit this pane-local sentinel and stop:

```text
STATUS: implement_blocked
BLOCK_REASON: <short_reason>
BLOCK_REASON_CODE: <reason_code>
REQUEST: verify_triage
ESCALATION_CLASS: verify_triage
HANDOFF: <active_handoff_path>
HANDOFF_SHA: <active_handoff_sha>
BLOCK_ID: <active_handoff_sha>:<short_reason>
```
