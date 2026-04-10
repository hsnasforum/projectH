# docs: core browser response-surface wording truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-core-browser-response-surface-wording-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, `docs/TASK_BACKLOG.md`의 browser response-surface stale wording을 현재 shipped truth와 맞게 고쳤는지 다시 확인해야 했습니다.
- same-day docs-only truth-sync가 이미 많이 반복된 상태라, 이번 라운드가 truthful하면 다음 slice는 같은 family의 남은 non-core residual을 한 번에 닫는 bounded bundle이어야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/PRODUCT_SPEC.md:1842`
  - `docs/ACCEPTANCE_CRITERIA.md:25`
  - `docs/ACCEPTANCE_CRITERIA.md:1360`
  - `docs/ARCHITECTURE.md:109`
  - `docs/ARCHITECTURE.md:1319`
  - `docs/ARCHITECTURE.md:1330`
  - `docs/ARCHITECTURE.md:1359`
  - `docs/TASK_BACKLOG.md:18`
- 현재 shipped UI/shell truth와도 맞습니다.
  - search preview surface
    - `app/static/app.js:1007`
    - `app/static/app.js:1014`
    - `app/static/app.js:1024`
  - source-type labels
    - `app/static/app.js:1257`
    - `app/static/app.js:1258`
  - evidence / summary meta
    - `app/static/app.js:1676`
    - `app/static/app.js:1677`
    - `app/static/app.js:2069`
  - progress / cancel surface
    - `app/templates/index.html:107`
    - `app/templates/index.html:119`
    - `app/templates/index.html:251`
- 다만 최신 `/work`의 `남은 리스크`는 약간 과합니다. 같은 family의 non-core residual이 더 남아 있습니다.
  - `README.md:114`
  - `docs/project-brief.md:15`
  - `docs/project-brief.md:74`
  - `docs/PRODUCT_PROPOSAL.md:54`
- `docs/project-brief.md:15`의 `streaming cancel`도 현재 contract bullet 기준으로는 stale wording입니다.
- 반면 `README.md:126`의 `streaming cancel`은 Playwright smoke scenario label이라, 이번 verification에서는 current surface summary drift로 바로 간주하지 않았습니다.

## 검증
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '1839,1843p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '22,29p;1358,1361p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '107,110p;1318,1331p;1357,1360p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '16,19p'`
- `rg -n --no-heading 'summary-range panel|streaming cancel|evidence and summary-range panels|Evidence/source panel and summary-range panel|evidence/source panel and summary-range panel|structured search result preview panel|summary source-type labels|summary span / applied-range panel|streaming progress \+ cancel' docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/TASK_BACKLOG.md docs/project-brief.md docs/PRODUCT_PROPOSAL.md README.md docs/MILESTONES.md docs/NEXT_STEPS.md`
- `nl -ba app/static/app.js | sed -n '999,1030p;1253,1260p;1674,1678p;2067,2073p'`
- `nl -ba app/templates/index.html | sed -n '107,121p;249,257p'`
- `nl -ba README.md | sed -n '110,127p'`
- `nl -ba docs/project-brief.md | sed -n '12,18p;72,76p'`
- `nl -ba docs/PRODUCT_PROPOSAL.md | sed -n '50,56p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '130,170p;971,981p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 current browser response-surface wording family는 아직 완전히 닫히지 않았습니다. 다음 라운드에서는 `README.md:114`, `docs/project-brief.md:15`, `docs/project-brief.md:74`, `docs/PRODUCT_PROPOSAL.md:54`를 한 묶음으로 맞추는 편이 적절합니다.
