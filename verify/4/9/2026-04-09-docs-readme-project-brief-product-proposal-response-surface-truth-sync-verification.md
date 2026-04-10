# docs: readme project-brief product-proposal response-surface truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-readme-project-brief-product-proposal-response-surface-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `README.md`, `docs/project-brief.md`, `docs/PRODUCT_PROPOSAL.md`의 browser response-surface residual wording을 현재 shipped truth와 맞게 고쳤는지 다시 확인해야 했습니다.
- same-day docs-only truth-sync가 이미 길게 이어진 상태라, 이번 라운드가 truthful하면 다음 slice는 남은 same-family root-doc residual을 한 번에 닫는 bounded bundle이어야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `README.md:114`
  - `docs/project-brief.md:15`
  - `docs/project-brief.md:74`
  - `docs/project-brief.md:75`
  - `docs/project-brief.md:76`
  - `docs/project-brief.md:77`
  - `docs/project-brief.md:79`
  - `docs/project-brief.md:80`
  - `docs/PRODUCT_PROPOSAL.md:54`
  - `docs/PRODUCT_PROPOSAL.md:55`
  - `docs/PRODUCT_PROPOSAL.md:56`
  - `docs/PRODUCT_PROPOSAL.md:57`
  - `docs/PRODUCT_PROPOSAL.md:59`
  - `docs/PRODUCT_PROPOSAL.md:60`
- 현재 shipped UI/shell truth와도 맞습니다.
  - search preview surface
    - `app/static/app.js:1007`
    - `app/static/app.js:1014`
    - `app/static/app.js:1024`
  - source-type labels and quick meta
    - `app/static/app.js:1257`
    - `app/static/app.js:1258`
    - `app/static/app.js:1668`
    - `app/static/app.js:1676`
    - `app/static/app.js:1677`
  - response-origin / source-type / applied-preferences meta
    - `app/frontend/src/components/MessageBubble.tsx:263`
    - `app/frontend/src/components/MessageBubble.tsx:270`
    - `app/frontend/src/components/MessageBubble.tsx:275`
    - `app/frontend/src/components/MessageBubble.tsx:280`
  - 같은 surface truth는 core docs에도 이미 맞춰져 있습니다.
    - `README.md:47`
    - `README.md:51`
    - `README.md:52`
    - `README.md:54`
    - `README.md:56`
    - `docs/PRODUCT_SPEC.md:103`
    - `docs/PRODUCT_SPEC.md:104`
    - `docs/PRODUCT_SPEC.md:334`
    - `docs/PRODUCT_SPEC.md:336`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다. same-family root docs residual이 아직 남아 있습니다.
  - `docs/PRODUCT_SPEC.md:135`
  - `docs/PRODUCT_SPEC.md:145`
  - `docs/PRODUCT_SPEC.md:1832`
  - `docs/ARCHITECTURE.md:44`
  - `docs/ARCHITECTURE.md:116`
- 남은 residual은 `summary-range` shorthand가 root docs의 metadata/selection/smoke-summary 문맥에 아직 남아 있는 경우입니다.
- `README.md:126`의 `streaming cancel`은 이번 verification에서 residual로 올리지 않았습니다. 현재 smoke scenario label 문맥이라 current browser response-surface summary drift와는 구분했습니다.

## 검증
- `git diff --check`
- `nl -ba README.md | sed -n '112,116p'`
- `nl -ba docs/project-brief.md | sed -n '13,16p;72,77p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '50,57p'`
- `rg -n --no-heading 'summary-range|streaming cancel|structured search result preview panel|summary source-type labels|applied-preferences badge|streaming progress \+ cancel' README.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '133,145p;1830,1833p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '42,46p;114,117p'`
- `nl -ba app/static/app.js | sed -n '1007,1028p;1255,1258p;1668,1677p'`
- `nl -ba app/frontend/src/components/MessageBubble.tsx | sed -n '263,280p'`
- `nl -ba README.md | sed -n '47,56p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '97,106p;332,336p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 current browser response-surface wording family는 root docs 기준으로 아직 완전히 닫히지 않았습니다. 다음 라운드에서는 `docs/PRODUCT_SPEC.md`와 `docs/ARCHITECTURE.md`의 `summary-range` metadata/selection/smoke-summary residual을 한 번에 맞추는 편이 적절합니다.
