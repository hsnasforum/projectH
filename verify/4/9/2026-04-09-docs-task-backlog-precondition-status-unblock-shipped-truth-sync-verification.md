# docs: TASK_BACKLOG precondition-status and unblock residual shipped wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-task-backlog-precondition-status-unblock-shipped-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 docs-only truth-sync가 실제 `docs/TASK_BACKLOG.md` 현재 상태와 shipped reviewed-memory contract truth에 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory shipped-layer family에서 더 이상 docs-only micro-loop를 늘리지 않도록, 남은 root-doc residual을 한 번에 닫는 다음 Claude 슬라이스를 다시 좁혀야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 2곳은 truthful합니다.
  - `docs/TASK_BACKLOG.md:329`
  - `docs/TASK_BACKLOG.md:476`
- 위 두 줄은 현재 shipped truth와 맞습니다.
  - blocked-only `reviewed_memory_precondition_status` 객체와 reviewed-memory apply path는 분리되어 있습니다.
  - current `reviewed_memory_capability_status.capability_outcome = unblocked_all_required`는 same-aggregate source-family-plus-basis path가 있을 때 이미 materialize됩니다.
- 이 direct sync는 root docs 및 구현 축과 맞습니다.
  - `docs/MILESTONES.md:199`
  - `docs/MILESTONES.md:275`
  - `docs/PRODUCT_SPEC.md:1498`
  - `docs/PRODUCT_SPEC.md:1537`
  - `docs/ARCHITECTURE.md:1140`
  - `docs/ARCHITECTURE.md:1164`
  - `app/handlers/aggregate.py:392`
  - `app/handlers/aggregate.py:554`
  - `tests/test_web_app.py:7300`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 shipped-layer family의 root docs에 stale wording이 남아 있습니다.
  - `docs/NEXT_STEPS.md:532`
  - `docs/NEXT_STEPS.md:536`
  - `docs/ARCHITECTURE.md:1138`
- 위 residual은 rollback / disable / conflict / operator-audit layer를 아직 미출하처럼 프레이밍하지만, 현재 repo는 read-only contract surfaces와 apply / stop-apply / reversal / conflict-visibility lifecycle을 이미 separate layer로 출하한 상태입니다.
- 다음 슬라이스는 `docs/NEXT_STEPS.md`와 `docs/ARCHITECTURE.md`의 remaining shipped-layer residual bundle로 고정했습니다.

## 검증
- `sed -n '1,220p' work/4/9/2026-04-09-docs-task-backlog-precondition-status-unblock-shipped-truth-sync.md`
- `sed -n '1,220p' verify/4/9/2026-04-09-docs-task-backlog-precondition-heading-shipped-truth-sync-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `ls -1t work/4/9/*.md | head -n 5`
- `ls -1t verify/4/9/*.md | head -n 5`
- `git diff --check`
- `git diff -- docs/TASK_BACKLOG.md`
- `rg -n "no reviewed-memory apply|through later machinery|no rollback / disable / conflict / operator-audit layer|no precondition-satisfying rollback / disable layer|capability_outcome = unblocked_all_required|blocked-only status object|apply path is shipped separately" docs/TASK_BACKLOG.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '324,480p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '528,537p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1496,1542p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1128,1170p'`
- `nl -ba docs/MILESTONES.md | sed -n '196,200p;273,276p'`
- `nl -ba app/handlers/aggregate.py | sed -n '388,404p;554,620p'`
- `nl -ba tests/test_web_app.py | sed -n '7286,7304p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 direct `TASK_BACKLOG` sync 자체는 truthful합니다.
- 다만 같은 reviewed-memory shipped-layer family의 root docs residual(`docs/NEXT_STEPS.md:532`, `docs/NEXT_STEPS.md:536`, `docs/ARCHITECTURE.md:1138`)이 남아 있으므로, 이번 라운드를 family 전체 closure로 보기는 어렵습니다.
