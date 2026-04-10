# docs: milestones next-steps browser response-surface summary truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-milestones-next-steps-browser-response-surface-summary-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`의 browser response-surface summary wording을 현재 shipped UI truth와 맞게 고쳤는지 다시 확인해야 했습니다.
- same-day docs-only truth-sync가 이미 길게 이어진 상태라, 이번 라운드가 truthful하면 다음 slice는 또 하나의 micro-fix가 아니라 남은 same-family core-doc residual을 한 번에 닫는 bounded bundle이어야 했습니다.

## 핵심 변경
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
  - `docs/MILESTONES.md:29`
  - `docs/NEXT_STEPS.md:10`
  - `docs/NEXT_STEPS.md:11`
  - `docs/NEXT_STEPS.md:12`
  - `docs/NEXT_STEPS.md:13`
  - `docs/NEXT_STEPS.md:16`
- 현재 shipped browser surface와도 맞습니다.
  - structured search result preview panel은 현재 shell transcript/response card에 렌더링됩니다.
    - `app/static/app.js:1007`
    - `app/static/app.js:1014`
    - `app/static/app.js:1024`
  - summary source-type label은 `문서 요약` / `선택 결과 요약`으로 계산됩니다.
    - `app/static/app.js:1257`
    - `app/static/app.js:1258`
  - summary/evidence quick-meta는 `근거 N개`, `요약 구간 N개`로 노출됩니다.
    - `app/static/app.js:1676`
    - `app/static/app.js:1677`
  - evidence/source panel과 progress/cancel surface도 현재 shell에 있습니다.
    - `app/static/app.js:2069`
    - `app/templates/index.html:107`
    - `app/templates/index.html:119`
    - `app/templates/index.html:251`
- 다만 최신 `/work`의 `남은 리스크 없음`은 과합니다. 같은 current browser response-surface family의 stale wording이 core docs에 더 남아 있습니다.
  - `docs/PRODUCT_SPEC.md:1842`
  - `docs/ACCEPTANCE_CRITERIA.md:25`
  - `docs/ACCEPTANCE_CRITERIA.md:1360`
  - `docs/ARCHITECTURE.md:109`
  - `docs/ARCHITECTURE.md:1319`
  - `docs/ARCHITECTURE.md:1330`
  - `docs/ARCHITECTURE.md:1358`
  - `docs/ARCHITECTURE.md:1359`
  - `docs/TASK_BACKLOG.md:18`
- 남아 있는 stale wording은 주로 `summary-range panel`, `streaming cancel`, `evidence and summary-range panels` 계열입니다.

## 검증
- `git diff --check`
- `git diff -- docs/MILESTONES.md docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '26,36p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '5,18p'`
- `rg -n --no-heading 'response cards and note preview|structured search result preview panel|source-role trust labels|summary source-type labels|summary span / applied-range panel|streaming progress \+ cancel|streaming cancel|summary-range panel' docs/MILESTONES.md docs/NEXT_STEPS.md README.md docs/PRODUCT_SPEC.md`
- `nl -ba app/static/app.js | sed -n '999,1030p;1253,1260p;1674,1678p;2067,2073p'`
- `nl -ba app/templates/index.html | sed -n '107,121p;249,257p'`
- `nl -ba README.md | sed -n '47,56p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '97,106p;332,336p;1839,1843p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '22,29p;1356,1362p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '104,111p;1316,1331p;1357,1361p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '16,20p'`
- Python unit test와 Playwright는 재실행하지 않았습니다. 최신 `/work`가 docs-only이고 code/test/runtime 변경을 주장하지 않았기 때문입니다.

## 남은 리스크
- 최신 `/work`의 직접 수정 대상은 truthful합니다.
- 다만 current browser response-surface naming family는 아직 완전히 닫히지 않았습니다. 다음 라운드에서는 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, `docs/TASK_BACKLOG.md`의 stale `summary-range panel` / `streaming cancel` / `evidence and summary-range panels` wording을 한 번에 맞추는 편이 적절합니다.
