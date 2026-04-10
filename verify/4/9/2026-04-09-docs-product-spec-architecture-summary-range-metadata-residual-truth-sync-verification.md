# docs: product-spec architecture summary-range metadata residual truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-product-spec-architecture-summary-range-metadata-residual-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`의 summary-range metadata residual wording을 현재 shipped truth와 맞게 고쳤는지 다시 확인해야 했습니다.
- root docs residual이 닫히면, 다음 slice는 같은 family의 instruction-surface omission을 한 번에 정리하는 쪽이 더 적절했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:135`
  - `docs/PRODUCT_SPEC.md:145`
  - `docs/PRODUCT_SPEC.md:1832`
  - `docs/ARCHITECTURE.md:44`
  - `docs/ARCHITECTURE.md:116`
- 현재 shipped UI/shell truth와도 맞습니다.
  - summary/evidence quick-meta와 panel surface
    - `app/static/app.js:1668`
    - `app/static/app.js:1676`
    - `app/static/app.js:1677`
    - `app/static/app.js:2069`
    - `app/templates/index.html:249`
    - `e2e/tests/web-smoke.spec.mjs:135`
  - search preview / source-type / applied-preferences meta surface
    - `app/static/app.js:1007`
    - `app/static/app.js:1014`
    - `app/static/app.js:1024`
    - `app/static/app.js:1257`
    - `app/static/app.js:1258`
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:270`
    - `app/frontend/src/components/MessageBubble.tsx:275`
- `summary-range` exact phrase는 docs/README/e2e/test scope 기준으로 사실상 닫혔습니다.
  - 남아 있는 `README.md:126`의 `streaming cancel`은 current browser response-surface summary drift가 아니라 smoke scenario label로 유지된 것입니다.
- 다만 최신 `/work`의 `남은 리스크 없음`은 약간 과합니다. same-family current product slice omission이 instruction docs에 남아 있습니다.
  - `AGENTS.md:29`
  - `AGENTS.md:35`
  - `AGENTS.md:36`
  - `AGENTS.md:37`
  - `CLAUDE.md:9`
  - `CLAUDE.md:14`
  - `CLAUDE.md:15`
- 두 파일은 아직 structured search result preview panel, summary source-type labels, applied-preferences badge를 current product/current implemented focus bullet에서 빠뜨리고 있습니다.

## 검증
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '133,145p;1830,1833p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '42,46p;114,117p'`
- `rg -n --no-heading 'summary-range|summary range|attach evidence/source and summary span / applied-range metadata|evidence/source and summary span / applied-range selection|evidence/source and summary span / applied-range metadata|file summary with evidence/source panel and summary span / applied-range panel' README.md docs -g '!docs/recycle/**'`
- `nl -ba app/static/app.js | sed -n '1668,1677p;2067,2069p'`
- `nl -ba app/templates/index.html | sed -n '249,257p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '135,154p'`
- `rg -n --no-heading 'structured search result preview panel|summary source-type label|applied-preferences badge' README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md`
- `nl -ba AGENTS.md | sed -n '27,42p'`
- `nl -ba CLAUDE.md | sed -n '9,20p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 same-family current product slice omission이 `AGENTS.md`와 `CLAUDE.md`에 남아 있으므로, 다음 라운드에서는 두 파일을 함께 맞추는 편이 적절합니다.
