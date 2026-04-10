# docs: TASK_BACKLOG reviewed-memory disable state-machine later wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-task-backlog-disable-state-machine-later-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `docs/TASK_BACKLOG.md` disable-state-machine later wording sync가 현재 code/docs truth와 맞는지 다시 확인해야 했습니다.
- 같은 reviewed-memory docs-only family의 false state-machine residual이 이번 라운드로 닫히면, 다음은 같은 family micro-slice가 아니라 새 user-visible docs axis로 넘어가야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/TASK_BACKLOG.md:365`
- 현재 문구는 shipped truth와 맞습니다.
  - `disable = stop-apply of applied reviewed-memory effect; the disable contract surface is shipped read-only and the stop-apply lifecycle (\`future_reviewed_memory_stop_apply\`) is shipped on \`record_stage\`; per-precondition disable satisfaction booleans remain later`
  - `app/handlers/aggregate.py:467`
  - `app/handlers/aggregate.py:470`
  - `docs/ARCHITECTURE.md:1165`
- root docs 기준으로 `disable state machine remains later` 잔여는 더 이상 보이지 않습니다.
- 따라서 reviewed-memory false state-machine-later wording family는 현재 root docs 기준으로 닫혔습니다.
- 다음 슬라이스는 새 user-visible docs axis가 적절합니다. 현재 frontend는 `applied_preferences`가 있을 때 assistant message meta에 `선호 N건 반영` badge를 이미 렌더링하지만, root docs는 field만 적고 이 visible badge를 설명하지 않습니다.
  - payload field and producer:
    - `core/agent_loop.py:6806`
    - `core/agent_loop.py:8541`
  - frontend consumer and visible badge:
    - `app/frontend/src/hooks/useChat.ts:214`
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:280`
  - current docs that mention `response_origin` badge or `applied_preferences` field without the current badge surface:
    - `README.md:53`
    - `docs/PRODUCT_SPEC.md:105`
    - `docs/PRODUCT_SPEC.md:313`
    - `docs/PRODUCT_SPEC.md:334`
    - `docs/ACCEPTANCE_CRITERIA.md:26`
    - `docs/ACCEPTANCE_CRITERIA.md:121`
    - `docs/ARCHITECTURE.md:156`
    - `docs/ARCHITECTURE.md:167`
    - `docs/ARCHITECTURE.md:1360`

## 검증
- `git diff --check`
- `rg -n --no-heading 'disable state machine remains later' docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '363,366p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '1164,1166p'`
- `nl -ba app/handlers/aggregate.py | sed -n '466,471p'`
- `rg -n --no-heading 'applied_preferences|선호 .*건 반영|response origin badge' README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md app/frontend/src/components/MessageBubble.tsx app/frontend/src/hooks/useChat.ts core/agent_loop.py`
- `nl -ba core/agent_loop.py | sed -n '6788,6815p;8528,8542p'`
- `nl -ba app/frontend/src/hooks/useChat.ts | sed -n '206,220p'`
- `nl -ba app/frontend/src/components/MessageBubble.tsx | sed -n '263,280p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- reviewed-memory false state-machine-later family는 닫혔습니다.
- 다만 current user-visible docs는 `applied_preferences`의 visible response-meta badge를 아직 명시하지 않으므로, 다음 라운드에서 README/root docs를 함께 맞추는 것이 적절합니다.
