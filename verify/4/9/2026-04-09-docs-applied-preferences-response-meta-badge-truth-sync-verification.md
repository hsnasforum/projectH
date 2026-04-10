# docs: applied-preferences response-meta badge truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-applied-preferences-response-meta-badge-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 applied-preferences response-meta badge docs sync가 현재 frontend/payload truth와 맞는지 다시 확인해야 했습니다.
- 이번 라운드가 truthful하면 같은 user-visible docs family 안에서 남아 있는 planning/status docs residual을 한 번에 다음 slice로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:54`
  - `docs/PRODUCT_SPEC.md:106`
  - `docs/PRODUCT_SPEC.md:314`
  - `docs/PRODUCT_SPEC.md:336`
  - `docs/ACCEPTANCE_CRITERIA.md:27`
  - `docs/ACCEPTANCE_CRITERIA.md:122`
  - `docs/ARCHITECTURE.md:156`
  - `docs/ARCHITECTURE.md:1361`
- 현재 shipped truth는 문서와 맞습니다.
  - `AgentResponse.applied_preferences`는 현재 응답 경로에서 생산됩니다.
    - `core/agent_loop.py:6806`
    - `core/agent_loop.py:8541`
  - frontend는 그 값을 assistant message에 전달합니다.
    - `app/frontend/src/hooks/useChat.ts:214`
  - assistant message meta 영역은 `applied_preferences`가 비어 있지 않을 때 `선호 N건 반영` badge와 tooltip을 렌더링합니다.
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:275`
    - `app/frontend/src/components/MessageBubble.tsx:280`
- 다만 최신 `/work`의 `남은 리스크 없음`은 약간 과합니다. 같은 user-visible docs family 안에 planning/status root docs residual이 남아 있습니다.
  - `docs/MILESTONES.md:32`
  - `docs/NEXT_STEPS.md:12`
- 두 문서는 current product bullet에서 여전히 `response origin badge`만 적고 있고, 방금 sync된 `applied-preferences` badge는 빠져 있습니다.

## 검증
- `git diff --check`
- `rg -n --no-heading 'applied_preferences|선호 .*건 반영' README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
- `nl -ba core/agent_loop.py | sed -n '6796,6807p;8532,8542p'`
- `nl -ba app/frontend/src/hooks/useChat.ts | sed -n '210,216p'`
- `nl -ba app/frontend/src/components/MessageBubble.tsx | sed -n '263,281p'`
- `nl -ba README.md | sed -n '52,55p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '104,106p;312,314p;333,336p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '26,27p;121,122p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '155,157p;1360,1361p'`
- `rg -n --no-heading 'response origin badge|applied_preferences|선호 N건 반영' docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `nl -ba docs/MILESTONES.md | sed -n '28,34p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '10,13p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 `docs/MILESTONES.md:32`와 `docs/NEXT_STEPS.md:12`가 current product bullet에서 applied-preferences badge를 아직 빠뜨리고 있으므로, 다음 라운드에서 두 파일을 함께 맞추는 것이 적절합니다.
