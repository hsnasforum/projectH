# docs: PRODUCT_SPEC MILESTONES reviewed-memory cross-session-counting sequencing truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-milestones-cross-session-counting-sequencing-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `docs/PRODUCT_SPEC.md` / `docs/MILESTONES.md` cross-session-counting sequencing wording sync가 현재 code/docs truth와 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 여러 번 반복됐으므로, 이번 라운드가 truthful하면 다음은 micro-slice가 아니라 남은 root-doc wording drift를 한 묶음으로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:1022`
  - `docs/MILESTONES.md:189`
- 위 문구는 현재 shipped truth anchor와 맞습니다.
  - `docs/PRODUCT_SPEC.md:1062`
  - `docs/PRODUCT_SPEC.md:1473`
  - `docs/PRODUCT_SPEC.md:1474`
  - `docs/ACCEPTANCE_CRITERIA.md:580`
  - `docs/ACCEPTANCE_CRITERIA.md:589`
  - `app/serializers.py:3902`
  - `app/serializers.py:1515`
  - `app/handlers/aggregate.py:393`
  - `app/handlers/aggregate.py:469`
  - `app/handlers/aggregate.py:531`
  - `tests/test_web_app.py:7245`
- 따라서 최신 `/work`가 겨냥한 cross-session-counting sequencing residual 자체는 닫혔습니다.
- 다만 같은 reviewed-memory docs family에는 아직 한 묶음의 current-risk wording drift가 남아 있습니다.
  - `docs/MILESTONES.md:193`
  - `docs/NEXT_STEPS.md:536`
  - `docs/TASK_BACKLOG.md:306`
- 위 문구들은 rollback / disable / operator-audit contract surface의 state machine 또는 satisfaction boolean이 아직 later라고 적고 있지만, 현재 shipped truth는 다릅니다.
  - reviewed-memory apply / stop-apply / reversal / conflict-visibility lifecycle는 이미 shipped입니다.
  - aggregate-level `reviewed_memory_capability_status.capability_outcome`도 이미 shipped이며 `unblocked_all_required`까지 도달합니다.
  - 따라서 다음 슬라이스는 이 later-wording residual을 root docs 한 묶음으로 닫는 bounded bundle이 적절합니다.

## 검증
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md docs/MILESTONES.md`
- `rg -n "cross-session|cross session|counting.*session|session.*counting|sequencing" docs/PRODUCT_SPEC.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `sed -n '1008,1072p' docs/PRODUCT_SPEC.md`
- `sed -n '180,205p' docs/MILESTONES.md`
- `sed -n '570,600p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '520,540p' docs/NEXT_STEPS.md`
- `rg -n "recurrence_aggregate_candidates|candidate_recurrence_key|aggregate_promotion_marker|reviewed_memory_precondition_status|reviewed_memory_boundary_draft" app core storage tests`
- `rg -n "aggregate-transition-apply|apply_result|reviewed_memory_active_effects|future_reviewed_memory_stop_apply|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility|effect_active|effect_stopped|effect_reversed" app core storage tests`
- `sed -n '360,620p' app/handlers/aggregate.py`
- `sed -n '3888,4075p' app/serializers.py`
- `rg -n "state machines remain later|rollback / disable contract surfaces are shipped as read-only|cross-session counting remains later|promotion and cross-session counting remain later|same-session layers .* apply lifecycle" docs`
- `sed -n '296,312p' docs/TASK_BACKLOG.md`
- `sed -n '532,540p' docs/NEXT_STEPS.md`
- `sed -n '188,204p' docs/MILESTONES.md`
- `rg -n "capability_outcome|unblocked_all_required|blocked_all_required" app/serializers.py tests/test_web_app.py tests/test_smoke.py`
- `sed -n '7238,7260p' tests/test_web_app.py`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 `PRODUCT_SPEC` / `MILESTONES` cross-session-counting sequencing sync 자체는 truthful합니다.
- 다만 root docs에는 reviewed-memory contract-state / capability-status later-wording residual이 남아 있으므로, 다음 라운드에서 `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`를 한 번에 정리하는 것이 적절합니다.
