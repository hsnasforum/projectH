# docs: root reviewed-memory aggregate lifecycle summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-root-aggregate-lifecycle-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 root-doc aggregate lifecycle summary sync가 현재 code/docs truth와 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 여러 번 반복됐으므로, 이번 라운드가 truthful하면 다음은 남은 정확한 residual 1개를 닫는 bounded slice로 바로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:60`
  - `docs/PRODUCT_SPEC.md:230`
  - `docs/ACCEPTANCE_CRITERIA.md:1358`
  - `docs/ARCHITECTURE.md:80`
  - `docs/ARCHITECTURE.md:1164`
  - `docs/ARCHITECTURE.md:1298`
  - `docs/ARCHITECTURE.md:1328`
  - `docs/MILESTONES.md:340`
  - `docs/TASK_BACKLOG.md:147`
  - `docs/TASK_BACKLOG.md:717`
- 위 summary 구간들은 현재 shipped lifecycle detail과 맞습니다.
  - stop-apply는 `record_stage = stopped`와 함께 `apply_result.result_stage = effect_stopped`를 기록합니다.
    - `app/handlers/aggregate.py:467`
    - `app/handlers/aggregate.py:470`
  - reversal은 `record_stage = reversed`와 함께 `apply_result.result_stage = effect_reversed`를 기록합니다.
    - `app/handlers/aggregate.py:529`
    - `app/handlers/aggregate.py:532`
  - conflict visibility는 separate record이며 `transition_action = future_reviewed_memory_conflict_visibility`, `source_apply_transition_ref`, `conflict_entries`, `conflict_entry_count`를 남깁니다.
    - `app/handlers/aggregate.py:639`
    - `app/handlers/aggregate.py:643`
    - `app/handlers/aggregate.py:644`
    - `app/handlers/aggregate.py:645`
- summary 축의 압축 패턴은 현재 root docs 대상 구간에서 보이지 않습니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 약간 과합니다. 같은 reviewed-memory root-doc family 안에 stale wording 1곳이 남아 있습니다.
  - `docs/TASK_BACKLOG.md:365`
- 위 문구는 `disable state machine remains later`라고 적지만, 현재 shipped truth는 이미 stop-apply lifecycle이 열려 있다는 것입니다.
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:470`
  - `docs/ARCHITECTURE.md:1165`

## 검증
- `git diff --check`
- `rg -n --no-heading 'removes the effect; reversal:|records a .*reviewed_memory_conflict_visibility_record.*conflict_visibility_checked' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading 'effect_stopped|effect_reversed|future_reviewed_memory_conflict_visibility|source_apply_transition_ref|conflict_entries|conflict_entry_count' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `rg -n --no-heading 'disable state machine remains later' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `nl -ba app/handlers/aggregate.py | sed -n '462,476p;525,545p;636,646p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '56,62p;228,232p;1529,1538p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1356,1359p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '78,82p;1162,1166p;1296,1300p;1326,1330p'`
- `nl -ba docs/MILESTONES.md | sed -n '338,342p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '145,148p;363,366p;715,719p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 aggregate lifecycle summary sync 자체는 truthful합니다.
- 다만 `docs/TASK_BACKLOG.md:365`의 disable-state-machine later wording이 현재 shipped stop-apply lifecycle과 어긋나 있으므로, 다음 라운드에서 이 single-file residual을 닫는 것이 적절합니다.
