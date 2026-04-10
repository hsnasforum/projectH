# docs: MILESTONES TASK_BACKLOG rollback-disable target-influence truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-milestones-task-backlog-rollback-disable-target-influence-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only truth-sync가 실제 planning docs와 root authority docs, 구현 스니펫 기준으로 맞는지 다시 확인해야 했습니다.
- 직전 same-day `/verify`와 `.pipeline/claude_handoff.md`는 이미 닫힌 residual을 다음 슬라이스로 가리키고 있어, persistent verification truth와 다음 Claude 작업 범위를 새로 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다.
  - `docs/MILESTONES.md:212`
  - `docs/MILESTONES.md:224`
  - `docs/TASK_BACKLOG.md:352`
  - `docs/TASK_BACKLOG.md:361`
  - `docs/TASK_BACKLOG.md:382`
  - `docs/TASK_BACKLOG.md:391`
  는 모두 현재 `applied reviewed-memory effect` / `applied reviewed-memory influence` 기준으로 정리되어 있습니다.
- 이전 `/verify`가 residual로 적어 두었던 `later applied reviewed-memory ...` 계열 잔여는 현재 repo 기준으로 닫혔습니다.
  - `rg -n 'later applied reviewed-memory|later applied reviewed-memory influence|later applied reviewed-memory effect' docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md app/handlers/aggregate.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md` 결과 0건
- root authority docs와 구현 스니펫도 현재 shipped semantics를 그대로 가리킵니다.
  - `docs/PRODUCT_SPEC.md:1137`
  - `docs/PRODUCT_SPEC.md:1145`
  - `docs/PRODUCT_SPEC.md:1473`
  - `docs/PRODUCT_SPEC.md:1531`
  - `docs/ARCHITECTURE.md:866`
  - `docs/ARCHITECTURE.md:872`
  - `docs/ACCEPTANCE_CRITERIA.md:589`
  - `app/handlers/aggregate.py:392`
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:529`
  - `app/handlers/aggregate.py:554`
  - `tests/test_web_app.py:7301`
  - `tests/test_web_app.py:7488`
  - `tests/test_web_app.py:7643`
- 다음 슬라이스는 또 하나의 더 작은 same-family docs-only micro-fix가 아니라, `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`에 남은 shipped-vs-later summary drift bundle로 고정했습니다.
  - `docs/MILESTONES.md:199`
  - `docs/MILESTONES.md:203`
  - `docs/TASK_BACKLOG.md:115`
  - `docs/TASK_BACKLOG.md:306`
  - `docs/TASK_BACKLOG.md:350`
  - `docs/TASK_BACKLOG.md:365`
  - `docs/TASK_BACKLOG.md:380`
  는 여전히 apply/stop-apply/reversal/conflict-visibility shipped 상태나 shipped read-only contract surface를 `later` 또는 not-yet-existing처럼 축소해 적고 있습니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-milestones-task-backlog-rollback-disable-target-influence-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-planning-rollback-disable-applied-effect-truth-sync-verification.md`
- `sed -n '1,240p' .pipeline/claude_handoff.md`
- `git diff --check`
- `git status --short`
- `ls -1t work/4/9/*.md | head -n 12`
- `ls -1t verify/4/9/*.md | head -n 12`
- `nl -ba docs/NEXT_STEPS.md | sed -n '132,141p'`
- `nl -ba docs/MILESTONES.md | sed -n '190,226p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '110,122p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '306,406p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1135,1148p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1470,1494p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1529,1541p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '864,875p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '588,598p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '647,657p'`
- `nl -ba app/handlers/aggregate.py | sed -n '388,620p'`
- `nl -ba tests/test_web_app.py | sed -n '7286,7302p'`
- `nl -ba tests/test_web_app.py | sed -n '7484,7490p'`
- `nl -ba tests/test_web_app.py | sed -n '7641,7646p'`
- `rg -n 'later applied reviewed-memory|applied reviewed-memory' docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
- `rg -n 'later applied reviewed-memory|later applied reviewed-memory influence|later applied reviewed-memory effect' docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md app/handlers/aggregate.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n 'before actual reviewed-memory apply result machinery exists|rollback, disable, and operator-audit rules remain later|disable = later stop-apply machinery|future rollback target only|future stop-apply target only|later reviewed-memory boundary draft|not reviewed-memory apply or cross-session counting' docs/MILESTONES.md docs/TASK_BACKLOG.md`
- Python unit test와 Playwright는 이번 검증 라운드에서 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`의 reviewed-memory precondition summary 일부는 아직 shipped apply path와 shipped read-only contract surface를 과도하게 later/future로 축소합니다.
- 직전 `/verify`와 기존 `.pipeline/claude_handoff.md`는 이미 닫힌 잔여를 가리키므로, 이후 자동화는 이 새 `/verify`와 갱신된 handoff를 기준으로 읽어야 합니다.
