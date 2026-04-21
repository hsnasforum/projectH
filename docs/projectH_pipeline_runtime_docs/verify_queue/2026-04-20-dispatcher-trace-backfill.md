# 2026-04-20 dispatcher trace backfill — queued verify-lane instruction

## 근거 control 체인
- Gemini advice: `.pipeline/gemini_advice.md` CONTROL_SEQ 572
- Gemini re-request: `.pipeline/gemini_request.md` CONTROL_SEQ 574
- Gemini advice (materialize): `.pipeline/gemini_advice.md` CONTROL_SEQ 575
- Claude handoff (materialize): `.pipeline/claude_handoff.md` CONTROL_SEQ 576
- Source `/work`: `work/4/20/2026-04-20-autonomy-key-stability-lock.md`
- Source `/verify`: `verify/4/20/2026-04-20-autonomy-key-stability-lock-verification.md`

## Trigger
- Next runtime dispatcher cycle writes `.pipeline/runs/<run_id>/events.jsonl` with >= 2 `dispatch_selection` events. Verify lane does NOT execute this instruction until that trigger condition is met.

## Target verify note
- `verify/4/20/2026-04-20-dispatcher-trace-backfill-verification.md` (to be written by the verify owner AFTER the trigger is met; not pre-populated).

## Items to validate (via `jq` / `grep` / direct read)
1. **Monotonicity** — `date_key` is non-decreasing across the `dispatch_selection` events in the order they appear in `events.jsonl`. Extract each event's `payload.date_key`; assert the resulting list is equal to its sorted form.
2. **Consistency** — for every `dispatch_selection` event, `payload["date_key"] == Path(payload["latest_work"]).name[:10]`. This cross-checks the seq 543/552/555 emit-vs-parse semantic at runtime.
3. **Sentinel** — for every `dispatch_selection` event where `payload["latest_verify"] == "—"`, both `payload["latest_verify_date_key"] == ""` and `payload["latest_verify_mtime"] == 0.0`. This exercises the seq 555 `"—"` branch defensively.
4. **Stability** — payload key order and cardinality match the seq 567 test-layer lock: `list(payload) == ["latest_work", "latest_verify", "date_key", "latest_work_mtime", "latest_verify_date_key", "latest_verify_mtime"]` (exactly 6 keys). Any drift here means production emit shape has been changed without coordinated test update.
5. **Autonomy invariants** — for any autonomy-related event whose payload carries a `decision_class` field, assert `decision_class in SUPPORTED_DECISION_CLASSES or decision_class == ""` (the seq 570 "canonical OR empty" invariant). Likely applicable to `control_operator_gated`, `autonomy_changed`, or similar events; verify owner enumerates relevant event_types at execution time.

## Expected grep/jq chain (reference; verify owner adjusts for actual run_id)
- `jq -c 'select(.event_type == "dispatch_selection") | .payload' .pipeline/runs/<run_id>/events.jsonl` — enumerate payloads.
- `jq -c 'select(.event_type == "dispatch_selection") | .payload.date_key' .pipeline/runs/<run_id>/events.jsonl` — monotonicity check.
- `jq -c 'select(.event_type == "dispatch_selection") | [.payload.latest_work, .payload.date_key]' .pipeline/runs/<run_id>/events.jsonl` — consistency cross-check (expect `.name[:10]` match).
- `jq -c 'select(.event_type == "dispatch_selection" and .payload.latest_verify == "—") | [.payload.latest_verify_date_key, .payload.latest_verify_mtime]' .pipeline/runs/<run_id>/events.jsonl` — sentinel check (expect `["", 0]` or `["", 0.0]`).
- `jq -c 'select(.event_type == "dispatch_selection") | .payload | keys' .pipeline/runs/<run_id>/events.jsonl` — key set check (may need to compare to ordered list separately if jq normalizes order).
- `jq -c 'select(.payload.decision_class != null) | .payload.decision_class' .pipeline/runs/<run_id>/events.jsonl | sort -u` — autonomy invariant check (expect all values canonical or empty).

## Scope boundary
- This file is a QUEUE entry only; the verification itself runs in a future `verify/<date>/` note after the trigger condition is met.
- This file must NOT be edited by the implement lane to report verification RESULTS — results go in the target verify note instead.
- When the trigger fires and the verify round executes this instruction, the verify owner may optionally annotate this file with a pointer to the executed verify note for cross-reference (append-only; do NOT rewrite).
