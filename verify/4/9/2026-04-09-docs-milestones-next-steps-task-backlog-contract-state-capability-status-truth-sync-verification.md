# docs: MILESTONES NEXT_STEPS TASK_BACKLOG reviewed-memory contract-state capability-status truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-milestones-next-steps-task-backlog-contract-state-capability-status-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md` contract-state / capability-status wording sync가 현재 code/docs truth와 맞는지 다시 확인해야 했습니다.
- 같은 날 reviewed-memory docs-only truth-sync가 이미 여러 번 반복됐으므로, 이번 라운드가 대상 문서 기준으로 truthful하면 남은 same-family drift를 한 파일 단위 bundle로 바로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상 3곳은 truthful합니다.
  - `docs/MILESTONES.md:193`
  - `docs/NEXT_STEPS.md:536`
  - `docs/TASK_BACKLOG.md:306`
- 위 문구들은 현재 shipped truth와 맞습니다.
  - `app/serializers.py:1515`
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:529`
  - `docs/PRODUCT_SPEC.md:1473`
  - `docs/PRODUCT_SPEC.md:1474`
  - `docs/ACCEPTANCE_CRITERIA.md:970`
  - `docs/TASK_BACKLOG.md:476`
- 따라서 최신 `/work`가 겨냥한 contract-state / capability-status later-wording residual은 대상 3문서 기준으로 닫혔습니다.
- 다만 root docs 같은 family 기준으로는 아직 완전히 닫히지 않았습니다.
  - `docs/ARCHITECTURE.md:1165`
  - `docs/ARCHITECTURE.md:1166`
- 위 두 줄은 아직 `no disable state machine` / `no rollback state machine`이라고 적고 있지만, 현재 shipped truth는 stop-apply / reversal lifecycle이 이미 구현되어 있다는 점입니다.
  - `future_reviewed_memory_stop_apply`는 shipped입니다.
  - `future_reviewed_memory_reversal`도 shipped입니다.
  - 따라서 최신 `/work`의 직접 수정은 truthful하지만, `## 남은 리스크`의 `없음`은 root-doc family 기준으로는 과합니다.

## 검증
- `git diff --check`
- `git diff -- docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `sed -n '188,198p' docs/MILESTONES.md`
- `sed -n '532,538p' docs/NEXT_STEPS.md`
- `sed -n '302,309p' docs/TASK_BACKLOG.md`
- `rg -n "state machines remain later|satisfaction booleans remain later|per-precondition satisfaction booleans|unblocked_all_required|capability-status path|capability_status|apply / stop-apply / reversal / conflict-visibility lifecycle" docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
- `sed -n '1470,1480p' docs/PRODUCT_SPEC.md`
- `sed -n '576,592p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '790,808p' docs/ARCHITECTURE.md`
- `sed -n '1508,1528p' app/serializers.py`
- `sed -n '388,538p' app/handlers/aggregate.py`
- `rg -n "no disable state machine|no rollback state machine|disable satisfaction booleans|rollback satisfaction booleans|resolver machinery remain later" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md docs/MILESTONES.md`
- `nl -ba docs/MILESTONES.md | sed -n '190,196p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '532,538p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '304,308p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1162,1168p'`
- `nl -ba app/serializers.py | sed -n '1512,1520p'`
- `nl -ba app/handlers/aggregate.py | sed -n '462,472p;525,533p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 `MILESTONES` / `NEXT_STEPS` / `TASK_BACKLOG` sync 자체는 truthful합니다.
- 다만 root docs에는 `docs/ARCHITECTURE.md:1165-1166` rollback/disable state-machine later wording residual이 남아 있으므로, 다음 라운드에서 `docs/ARCHITECTURE.md` 한 파일 bundle로 닫는 것이 적절합니다.
