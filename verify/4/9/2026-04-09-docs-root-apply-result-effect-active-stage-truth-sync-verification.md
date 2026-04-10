# docs: root reviewed-memory apply-result effect-active stage truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-root-apply-result-effect-active-stage-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 root-doc `effect_active` stage sync가 현재 code/docs truth와 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 여러 번 반복됐으므로, 최신 `/work`가 truthful하면 다음은 더 작은 micro-slice가 아니라 남은 root-doc summary drift를 한 bundle로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/PRODUCT_SPEC.md:230`
  - `docs/PRODUCT_SPEC.md:1537`
  - `docs/ACCEPTANCE_CRITERIA.md:923`
  - `docs/ACCEPTANCE_CRITERIA.md:930`
  - `docs/ACCEPTANCE_CRITERIA.md:1358`
  - `docs/ARCHITECTURE.md:80`
  - `docs/ARCHITECTURE.md:1164`
  - `docs/ARCHITECTURE.md:1298`
  - `docs/ARCHITECTURE.md:1328`
  - `docs/MILESTONES.md:45`
  - `docs/MILESTONES.md:340`
  - `docs/NEXT_STEPS.md:16`
  - `docs/NEXT_STEPS.md:419`
  - `docs/TASK_BACKLOG.md:147`
  - `docs/TASK_BACKLOG.md:717`
- root docs 기준으로 `result_stage = result_recorded_effect_pending` 잔여는 더 이상 남아 있지 않습니다.
- 현재 shipped truth는 `결과 확정` 시점에 바로 `apply_result.result_stage = effect_active`를 기록하는 것입니다.
  - `app/handlers/aggregate.py:392`
  - `app/handlers/aggregate.py:399`
- 다만 최신 `/work`의 `남은 리스크 없음`은 약간 과합니다. 같은 root-doc family 안에 aggregate lifecycle summary drift가 4곳 남아 있습니다.
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/ARCHITECTURE.md:80`
  - `docs/ACCEPTANCE_CRITERIA.md:1358`
  - `docs/TASK_BACKLOG.md:147`
- 위 4곳은 `effect_active`까지는 맞췄지만, stop-apply / reversal / conflict-visibility를 축약하면서 현재 shipped detail 일부를 다시 생략합니다.
  - stop-apply는 `record_stage = stopped`뿐 아니라 `apply_result.result_stage = effect_stopped`를 함께 기록합니다.
    - `app/handlers/aggregate.py:467`
    - `app/handlers/aggregate.py:470`
  - reversal은 `record_stage = reversed`뿐 아니라 `apply_result.result_stage = effect_reversed`를 함께 기록합니다.
    - `app/handlers/aggregate.py:529`
    - `app/handlers/aggregate.py:532`
  - conflict visibility는 apply record mutation이 아니라 separate record이며 `source_apply_transition_ref`, `conflict_entries`, `conflict_entry_count`를 남깁니다.
    - `app/handlers/aggregate.py:639`
    - `app/handlers/aggregate.py:643`
    - `app/handlers/aggregate.py:644`
    - `app/handlers/aggregate.py:645`

## 검증
- `git diff --check`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading -o "result_stage = result_recorded_effect_pending" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading -o "result_stage = effect_active" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading "stop-apply:" docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `nl -ba app/handlers/aggregate.py | sed -n '390,402p'`
- `nl -ba app/handlers/aggregate.py | sed -n '458,538p'`
- `rg -n --no-heading "source_apply_transition_ref|conflict_entries|conflict_entry_count|future_reviewed_memory_conflict_visibility" app/handlers/aggregate.py app/serializers.py tests/test_web_app.py`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 root docs 4곳의 reviewed-memory aggregate lifecycle summary가 현재 stop-apply / reversal / conflict-visibility detail을 축약하고 있으므로, 다음 라운드에서 이 bundle을 한 번에 정리하는 것이 적절합니다.
