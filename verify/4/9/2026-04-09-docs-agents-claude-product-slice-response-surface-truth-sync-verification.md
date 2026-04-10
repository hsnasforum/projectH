# docs: agents claude product slice response-surface truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-agents-claude-product-slice-response-surface-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `AGENTS.md`, `CLAUDE.md`의 current product slice / current implemented focus 문구를 현재 shipped browser response surface와 맞게 정리했는지 다시 확인해야 했습니다.
- 같은 instruction-doc response-surface family가 실제로 닫혔는지 확인한 뒤, residual이 남아 있으면 그 한 묶음만 다음 slice로 넘겨야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `AGENTS.md:35`
  - `AGENTS.md:36`
  - `AGENTS.md:37`
  - `AGENTS.md:38`
  - `AGENTS.md:40`
  - `CLAUDE.md:14`
  - `CLAUDE.md:15`
  - `CLAUDE.md:16`
  - `CLAUDE.md:17`
  - `CLAUDE.md:19`
- 현재 문구는 shipped UI truth와 맞습니다.
  - structured search result preview panel:
    - `app/static/app.js:1007`
    - `app/static/app.js:1014`
    - `app/static/app.js:1024`
  - summary source-type labels:
    - `app/static/app.js:1257`
    - `app/static/app.js:1258`
    - `app/frontend/src/components/MessageBubble.tsx:270`
  - applied-preferences badge:
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:275`
    - `app/frontend/src/components/MessageBubble.tsx:280`
  - same surface family is already synced in source-of-truth docs:
    - `README.md:54`
    - `docs/PRODUCT_SPEC.md:106`
    - `docs/ACCEPTANCE_CRITERIA.md:27`
    - `docs/MILESTONES.md:33`
    - `docs/NEXT_STEPS.md:13`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다.
  - 같은 instruction-doc family residual이 `PROJECT_CUSTOM_INSTRUCTIONS.md`에 남아 있습니다.
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:6`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:12`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:13`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:14`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:18`
- 이 파일은 아직 `근거/출처 패널`, `요약 반영 구간 패널`, `response origin 배지` 정도로만 축약하고 있어 `source-role trust labels`, `structured search result preview panel`, `summary source-type labels`, `applied-preferences badge`를 빠뜨립니다.
- `GEMINI.md`는 current-product bullet 섹션이 아니라 arbitration role 문서라 같은 residual 범위로 잡지 않았습니다.
- 따라서 instruction-doc current product response-surface family는 아직 완전히 닫히지 않았고, 다음 라운드는 `PROJECT_CUSTOM_INSTRUCTIONS.md` 한 파일로 남은 drift를 닫는 편이 가장 좁고 coherent합니다.

## 검증
- `git diff --check`
- `git diff -- AGENTS.md CLAUDE.md`
- `nl -ba CLAUDE.md | sed -n '5,22p'`
- `rg -n --no-heading 'structured search result preview panel|summary source-type label|applied-preferences badge' README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `nl -ba app/static/app.js | sed -n '1007,1028p;1255,1258p;1668,1677p'`
- `nl -ba app/frontend/src/components/MessageBubble.tsx | sed -n '263,280p'`
- `nl -ba GEMINI.md | sed -n '1,80p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '1,120p'`
- `rg -n --no-heading 'structured search result preview panel|summary source-type labels|applied-preferences badge|summary span / applied-range panel|source-role trust labels' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md`
- `rg -n --no-heading '근거/출처 패널|요약 반영 구간 패널|response origin 배지|claim coverage / verification 상태' PROJECT_CUSTOM_INSTRUCTIONS.md`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 instruction-doc same-family residual이 `PROJECT_CUSTOM_INSTRUCTIONS.md`에 남아 있으므로 최신 `/work`의 `남은 리스크 없음`은 그대로 수용하기 어렵습니다.
- 다음 라운드에서 `PROJECT_CUSTOM_INSTRUCTIONS.md` current product slice wording을 shipped response-surface truth에 맞추면 이 family는 닫힙니다.
