# 2026-04-20 dispatcher trace backfill verification

## 변경 파일
- `verify/4/20/2026-04-20-dispatcher-trace-backfill-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`: operator가 `VERIFY_FIRST_THEN_CLOSE_BRANCH` 경로를 승인한 뒤, queued verify-lane 항목을 실제 runtime trace에 대조하고 다음 implement handoff를 좁게 고정했습니다.

## 변경 이유
- `docs/projectH_pipeline_runtime_docs/verify_queue/2026-04-20-dispatcher-trace-backfill.md`가 요구한 dispatcher trace backfill 검증을 실행했습니다.
- 현재 live run `.pipeline/runs/20260421T051027Z-p63257/events.jsonl`가 `dispatch_selection` 2건 이상 조건을 만족하므로, 과거 trigger run 대신 현재 run을 검증 대상으로 삼았습니다.
- 검증 중 `decision_class` canonical invariant가 실제로 깨진 것을 확인해 다음 implement slice를 operator-control metadata canonicalization으로 고정했습니다.

## 핵심 변경
- `dispatch_selection` 이벤트의 날짜 단조성, `latest_work` 기반 `date_key` 일치, `latest_verify == "—"` sentinel branch, 6-key payload shape/order는 모두 통과했습니다.
- autonomy payload invariant는 실패했습니다. `autonomy_changed` event seq 821이 `decision_class='branch_closure_and_milestone_transition'`를 싣고 있었고, 이 값은 `SUPPORTED_DECISION_CLASSES`에 없습니다.
- 같은 이벤트의 `classification_source='metadata_fallback'`도 확인했습니다. 원인은 `.pipeline/operator_request.md` seq 617의 `OPERATOR_POLICY: stop_until_operator_decision`과 `DECISION_CLASS: branch_closure_and_milestone_transition`가 canonical metadata로 정규화되지 않은 채 runtime event까지 흘러간 것입니다.
- 다음 control은 `.pipeline/claude_handoff.md` `CONTROL_SEQ: 618`로 작성해, implement owner가 이 metadata canonicalization을 먼저 고치게 했습니다.

## 검증
- `python3 - <<'PY' ...`
  - 대상: `.pipeline/runs/20260421T051027Z-p63257/events.jsonl`
  - `total_events=1376`
  - `dispatch_selection_count=1329`
  - `monotonic=True`
  - `consistency_failures=0`
  - `sentinel_count=275`
  - `sentinel_failures=0`
  - `stability_failures=0`
  - `decision_classes=['', 'branch_closure_and_milestone_transition']`
  - `invalid_decision_classes=['branch_closure_and_milestone_transition']`
  - `operator_policies=['', 'immediate_publish']`
  - `invalid_operator_policies=[]`
  - `normalize_stop_until_operator_decision=stop_until_operator_decision`
- `python3 - <<'PY' ...`
  - 첫 invalid context:
    - `seq=821`
    - `event_type=autonomy_changed`
    - `mode='needs_operator'`
    - `block_reason='branch_complete_pending_milestone_transition'`
    - `reason_code='branch_complete_pending_milestone_transition'`
    - `operator_policy='immediate_publish'`
    - `decision_class='branch_closure_and_milestone_transition'`
    - `classification_source='metadata_fallback'`

## 남은 리스크
- 이번 verify round는 결과 기록과 next-control 작성만 수행했고 production code는 고치지 않았습니다.
- 기존 run의 과거 event seq 821은 기록으로 남습니다. 다음 implement slice는 future emission과 writer validation을 고치는 범위입니다.
- `AXIS-G6-TEST-WEB-APP`와 `AXIS-G4 end-to-end`는 operator가 승인한 순서상 dispatcher trace blocker 해결 뒤 계속 pending입니다.
- 전체 pytest와 Playwright는 이번 verify-lane trace check 범위가 아니라 실행하지 않았습니다.
