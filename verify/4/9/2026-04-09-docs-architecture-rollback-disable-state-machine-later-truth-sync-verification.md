# docs: ARCHITECTURE reviewed-memory rollback-disable state-machine later wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-architecture-rollback-disable-state-machine-later-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `docs/ARCHITECTURE.md` rollback/disable state-machine later wording sync가 현재 code/docs truth와 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 여러 번 반복됐으므로, 이번 라운드가 truthful하면 다음은 더 작은 micro-slice가 아니라 남은 root-doc wording drift를 한 bundle로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상 2곳은 truthful합니다.
  - `docs/ARCHITECTURE.md:1165`
  - `docs/ARCHITECTURE.md:1166`
- 위 문구는 현재 shipped truth와 맞습니다.
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:529`
  - `docs/ARCHITECTURE.md:1162`
  - `docs/ARCHITECTURE.md:1164`
- 따라서 ARCHITECTURE의 rollback/disable state-machine later stale wording family는 닫혔습니다.
- 다만 root docs 전체 기준으로는 같은 reviewed-memory apply-result family에 더 큰 wording drift가 남아 있습니다.
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
- 위 구간들은 `결과 확정` 이후 `apply_result.result_stage = result_recorded_effect_pending`라고 적으면서 같은 문단에서 곧바로 `effect_active`를 말하고 있어 현재 코드와 어긋납니다.
  - 실제 구현은 `결과 확정` 시점에 `apply_result.result_stage = effect_active`를 바로 기록합니다.
  - `app/handlers/aggregate.py:392`
  - `app/handlers/aggregate.py:399`

## 검증
- `git diff --check`
- `git diff -- docs/ARCHITECTURE.md`
- `sed -n '1160,1168p' docs/ARCHITECTURE.md`
- `rg -n "no disable state machine|no rollback state machine|disable satisfaction booleans|rollback satisfaction booleans" docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `nl -ba app/handlers/aggregate.py | sed -n '462,472p;525,533p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1162,1168p'`
- `rg -n "result_stage = result_recorded_effect_pending|effect_active|effect_stopped|effect_reversed|apply_result" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `sed -n '1528,1542p' docs/PRODUCT_SPEC.md`
- `sed -n '916,936p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '1158,1168p' docs/ARCHITECTURE.md`
- `nl -ba app/handlers/aggregate.py | sed -n '390,402p'`
- `rg -n --no-heading -o "result_stage = result_recorded_effect_pending" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 `ARCHITECTURE` sync 자체는 truthful합니다.
- 다만 root docs에는 `결과 확정` 이후 `apply_result.result_stage`를 아직 `result_recorded_effect_pending`로 적는 bundle이 남아 있으므로, 다음 라운드에서 root docs 6파일을 한 번에 정리하는 것이 적절합니다.
