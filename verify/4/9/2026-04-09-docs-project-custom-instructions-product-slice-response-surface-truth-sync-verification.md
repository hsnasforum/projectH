# docs: project custom instructions product slice response-surface truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-project-custom-instructions-product-slice-response-surface-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `PROJECT_CUSTOM_INSTRUCTIONS.md`의 current product slice wording을 현재 shipped browser response surface와 맞게 정리했는지 다시 확인해야 했습니다.
- 같은 instruction-doc response-surface family가 이번 라운드로 실제로 닫히면, 다음은 더 작은 same-family micro-slice가 아니라 새로운 current-contract summary family로 넘어가야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:12`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:13`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:14`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:15`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md:17`
- 현재 문구는 shipped UI truth와 맞습니다.
  - evidence/source panel with source-role trust labels:
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:12`
    - `AGENTS.md:35`
    - `CLAUDE.md:14`
  - structured search result preview panel:
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:13`
    - `app/static/app.js:1007`
    - `app/static/app.js:1014`
    - `app/static/app.js:1024`
  - summary source-type labels:
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:14`
    - `app/static/app.js:1257`
    - `app/static/app.js:1258`
    - `app/frontend/src/components/MessageBubble.tsx:270`
  - summary span / applied-range wording:
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:15`
    - `AGENTS.md:38`
    - `CLAUDE.md:17`
  - applied-preferences badge:
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:17`
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:275`
    - `app/frontend/src/components/MessageBubble.tsx:280`
- 따라서 current product slice response-surface family는 instruction docs 기준으로 닫혔습니다.
  - `AGENTS.md`
  - `CLAUDE.md`
  - `PROJECT_CUSTOM_INSTRUCTIONS.md`
- 최신 `/work`의 `GEMINI.md에 동일 패턴 잔여 가능` 메모는 보수적 주석 수준으로는 괜찮지만, 현재 residual로 승격할 필요는 없습니다.
  - `GEMINI.md`는 current product slice bullet 문서가 아니라 arbitration-role 문서입니다.
- 다음 residual은 same-family response-surface가 아니라 instruction docs의 web-investigation current-contract summary 축약입니다.
  - 현재 instruction docs는 아래 수준으로만 적고 있습니다.
    - `AGENTS.md:43`
    - `AGENTS.md:44`
    - `CLAUDE.md:22`
    - `CLAUDE.md:23`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:20`
    - `PROJECT_CUSTOM_INSTRUCTIONS.md:21`
  - 반면 source-of-truth docs는 이미 shipped detail을 더 구체적으로 적고 있습니다.
    - `docs/project-brief.md:15`
    - `docs/project-brief.md:83`
    - `docs/project-brief.md:84`
    - `docs/PRODUCT_PROPOSAL.md:26`
    - `docs/PRODUCT_PROPOSAL.md:63`
    - `docs/PRODUCT_PROPOSAL.md:64`
    - `docs/PRODUCT_PROPOSAL.md:65`
    - `docs/NEXT_STEPS.md:18`
- 다음 슬라이스는 `AGENTS.md`, `CLAUDE.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`를 한 번에 묶어 web investigation의 shipped current surface를 더 정확히 적는 bounded bundle이 가장 적절합니다.

## 검증
- `git diff --check`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '1,30p'`
- `git diff -- PROJECT_CUSTOM_INSTRUCTIONS.md`
- `rg -n --no-heading 'source-role trust labels|structured search result preview panel|summary source-type labels|applied-preferences badge|summary span / applied-range' AGENTS.md CLAUDE.md PROJECT_CUSTOM_INSTRUCTIONS.md`
- `nl -ba app/static/app.js | sed -n '1007,1028p;1255,1258p'`
- `nl -ba app/frontend/src/components/MessageBubble.tsx | sed -n '263,280p'`
- `nl -ba AGENTS.md | sed -n '41,46p'`
- `nl -ba CLAUDE.md | sed -n '20,25p'`
- `nl -ba PROJECT_CUSTOM_INSTRUCTIONS.md | sed -n '18,22p'`
- `nl -ba docs/project-brief.md | sed -n '13,16p;81,84p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '24,27p;61,65p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,19p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- current product slice response-surface family는 instruction docs 기준으로 닫혔습니다.
- 다만 instruction docs의 web-investigation current-contract summary는 여전히 source-of-truth docs보다 축약돼 있으므로, 다음 라운드에서 세 파일을 한 묶음으로 맞추는 편이 적절합니다.
