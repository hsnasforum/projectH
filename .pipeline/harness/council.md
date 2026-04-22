# Council Protocol

This file is not a fourth agent. It is the convergence protocol used when
implement, verify, and advisory evidence must be reduced to one next control.

## Authority

This file is not a control slot and is not current truth. If it conflicts with
the active control slot, latest `/work`, latest `/verify`, or supervisor
`status.json` / `events.jsonl`, follow that current truth first.

## Trigger

Use this protocol when:

- implement reports `STATUS: implement_blocked`
- advisory is stale, incomplete, or inconclusive
- verify sees multiple plausible next slices
- a menu or labeled choice appears without real-risk metadata
- the current work drifts away from the active operator priority
- the same incident family repeats

## Inputs

- Current control slot and `CONTROL_SEQ`
- Latest `/work` and `/verify`
- Advisory request/advice when present
- Supervisor `status.json` and recent `events.jsonl` when runtime state matters
- Current docs or milestone paths named by the active request

## Method

1. Restate the current priority and active role boundary.
2. List at most three candidate actions.
3. Reject candidates that require real operator approval.
4. Rank remaining candidates by current-risk reduction, user-visible value,
   verification cost, and scope containment.
5. Produce one control action. If none is safe, produce one operator stop with
   structured metadata.

## Output Shape

```text
COUNCIL_DECISION: implement | advisory_followup | verify_followup | operator_required
REASON_CODE: <canonical_reason>
OWNER_ROLE: implement | verify | advisory | operator
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md | .pipeline/advisory_request.md | .pipeline/operator_request.md
NEXT_CONTROL_SEQ: <seq>
EVIDENCE:
- <path or runtime evidence>
REJECTED:
- <candidate>: <why rejected>
```

## Guardrails

- Do not call the user for ordinary ambiguity, context rollover, stale advisory,
  or menu choices.
- Do not create another long advisory loop if verify can make a bounded
  decision from current evidence.
- Do not add hardcoded vendor names or exact pane/control prose to runtime
  logic.
- Do not split the same incident into more file-local exceptions. Move repeated
  truth into a shared helper, replay test, or documented runtime surface.
