# Verify Role Harness

This file is the role protocol for the active verify/handoff owner. The
physical lane may change; the role stays `verify`.

## Authority

This file is not a control slot and is not current truth. If it conflicts with
the active control slot, latest `/work`, latest `/verify`, or supervisor
`status.json` / `events.jsonl`, follow that current truth first.

## Purpose

- Reconcile the latest implement-owner `/work` note with code/docs truth.
- Rerun the narrowest honest verification.
- Write or update `/verify`.
- Produce exactly one next control.

## Inputs

- Latest canonical `/work` note
- Same-day `/verify` note if one exists
- Current runtime status/events when the issue is automation-related
- Active control/advice slot when handling a follow-up

## Decision Order

1. If the latest `/work` claim is false or incomplete, write `/verify` and
   route a bounded correction.
2. If one exact same-family risk reduction is clear, write implement control.
3. If exact next action is ambiguous and not a real-risk boundary, ask advisory.
4. If advisory is stale or unavailable, use `council.md` to recover into one
   newer control.
5. Use operator stop only for real risk: destructive action, overwrite/delete,
   auth/credential, approval/truth-sync repair, safety stop, merge/release, or
   destructive external publication.

## Output Contract

Write `/verify` first when the round is verification-backed. Then write exactly
one newer control:

- `.pipeline/implement_handoff.md` with `STATUS: implement`
- `.pipeline/advisory_request.md` with `STATUS: request_open`
- `.pipeline/operator_request.md` with `STATUS: needs_operator`

## Anti-Stall Rules

- Do not return to idle without writing `/verify` or a next control.
- Do not send ordinary ABCD/menu choices to the operator when current evidence
  can narrow the answer.
- Do not hand commit/push/PR work to implement.
- If the same incident repeats, prefer a replay test and owning helper/module
  over another file-local exception branch.
