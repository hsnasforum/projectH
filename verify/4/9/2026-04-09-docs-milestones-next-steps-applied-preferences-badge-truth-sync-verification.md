# docs: milestones next-steps applied-preferences badge truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-milestones-next-steps-applied-preferences-badge-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`의 applied-preferences badge 문구를 현재 shipped UI/payload truth와 맞게 고쳤는지 다시 확인해야 했습니다.
- 같은 user-visible docs family가 이번 라운드에서 실제로 닫히면, 다음 라운드는 더 작은 badge micro-slice가 아니라 top-level shipped surface summary residual로 넘어가야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/MILESTONES.md:33`
  - `docs/NEXT_STEPS.md:13`
- 현재 shipped truth와도 맞습니다.
  - 응답 payload는 `applied_preferences`를 현재 응답 경로에서 채웁니다.
    - `core/agent_loop.py:6806`
    - `core/agent_loop.py:8541`
  - frontend는 해당 값을 assistant message에 전달합니다.
    - `app/frontend/src/hooks/useChat.ts:214`
  - assistant message meta 영역은 `applied_preferences`가 비어 있지 않을 때 `선호 N건 반영` badge와 tooltip을 렌더링합니다.
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:275`
    - `app/frontend/src/components/MessageBubble.tsx:280`
- 따라서 root docs의 applied-preferences response-meta badge family는 현재 기준으로 닫혔습니다.
  - `README.md:54`
  - `docs/PRODUCT_SPEC.md:106`
  - `docs/PRODUCT_SPEC.md:336`
  - `docs/ACCEPTANCE_CRITERIA.md:27`
  - `docs/ARCHITECTURE.md:156`
  - `docs/MILESTONES.md:33`
  - `docs/NEXT_STEPS.md:13`
- 다음 residual은 같은 badge family가 아니라 planning/status docs의 top-level browser MVP summary 축약입니다.
  - `docs/MILESTONES.md:29`
  - `docs/NEXT_STEPS.md:10`
  - `docs/NEXT_STEPS.md:11`
  - `docs/NEXT_STEPS.md:14`
- 현재 shipped shell은 이미 structured search result preview, summary source-type labels, evidence/source and summary-range metadata, streaming progress+cancel surface를 보여 주므로 다음 slice는 그 summary wording을 맞추는 편이 더 적절합니다.

## 검증
- `git diff --check`
- `git diff -- docs/MILESTONES.md docs/NEXT_STEPS.md`
- `rg -n --no-heading 'applied-preferences badge|선호 .*건 반영' docs/MILESTONES.md docs/NEXT_STEPS.md`
- `rg -n --no-heading 'applied-preferences badge|선호 .*건 반영' README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '26,34p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '5,16p'`
- `nl -ba core/agent_loop.py | sed -n '6796,6807p;8539,8542p'`
- `nl -ba app/frontend/src/hooks/useChat.ts | sed -n '210,216p'`
- `nl -ba app/frontend/src/components/MessageBubble.tsx | sed -n '263,281p'`
- `rg -n --no-heading '응답 생성 중|응답 취소|근거|요약 구간|문서 요약|선택 결과 요약|search_results' app/templates/index.html app/static/app.js`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 applied-preferences badge sync는 truthful하며 같은 family는 닫혔습니다.
- 다만 `docs/MILESTONES.md`와 `docs/NEXT_STEPS.md`의 top-level current browser summary는 아직 structured search preview, source-type labels, progress/cancel wording을 현재 shipped surface보다 더 좁게 적고 있으므로 다음 라운드에서 두 파일을 한 묶음으로 맞추는 편이 적절합니다.
