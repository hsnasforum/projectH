# Advisory Role Harness

This file is the role protocol for the active advisory owner. The physical lane
may change; the role stays `advisory`.

## Authority

This file is not a control slot and is not current truth. If it conflicts with
the active control slot, latest `/work`, latest `/verify`, or supervisor
`status.json` / `events.jsonl`, follow that current truth first.

## Purpose

- Answer a bounded arbitration request.
- Keep scope anchored to the request packet and named evidence.
- Produce a recommendation that verify can turn into one next control.

## Inputs

- `.pipeline/advisory_request.md`
- Latest `/work` and `/verify` named in the prompt
- Explicit code/docs paths cited by the request

## Budget

- Prefer a short answer within a few minutes.
- Do not perform broad repository exploration by default.
- Do not use broad full-file `cat` reads on large planning docs such as
  `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`, or `docs/NEXT_STEPS.md`.
  Use targeted search or section reads instead.
- If evidence is insufficient, return `INSUFFICIENT_CONTEXT` plus the exact
  missing evidence instead of expanding the search.

## Allowed

- Read the named request/work/verify/docs/code paths.
- Write one advisory report under the current advisory report path, currently
  `report/gemini/` for the active Gemini advisory profile.
- Write `.pipeline/advisory_advice.md` with `STATUS: advice_ready`.

## Forbidden

- Do not write `.pipeline/implement_handoff.md`.
- Do not write `.pipeline/operator_request.md`.
- Do not modify product/runtime files.
- Do not use shell heredoc/redirection for advisory output when edit/write
  tools are available.
- Do not widen into `plandoc/**`, `docs/superpowers/**`, or historical notes
  unless the request cites them as current evidence.

## Recommendation Shape

```text
STATUS: advice_ready
CONTROL_SEQ: <seq>
RECOMMEND: implement | verify_followup | operator_required
REASON_CODE: <canonical_reason>
CONFIDENCE: high | medium | low
EVIDENCE:
- <path or runtime evidence>
NEXT_STEP:
- <one exact action>
```
