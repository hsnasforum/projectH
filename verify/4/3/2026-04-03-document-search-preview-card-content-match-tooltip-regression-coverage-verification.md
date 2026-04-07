## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-content-match-tooltip-regression-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-content-match-tooltip-regression-coverage.md`가 직전 `/verify`가 넘긴 content-match tooltip current-risk를 실제로 닫았는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-content-match-snippet-regression-coverage-verification.md`가 다음 exact slice로 잡았던 `document-search preview-card content-match tooltip regression coverage`가 current tree와 rerun 결과에 truthful한지도 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 코드 변경과 browser rerun 주장은 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 search-only 시나리오에는 실제로 response detail/transcript 양쪽 second card에 대해 `.search-preview-name`의 `title` attribute가 `.../memo.md`로 끝나는지 확인하는 assertion이 추가되어 있습니다.
  - 재실행한 `make e2e-test`도 `17 passed (2.1m)`로 통과해 latest `/work`의 rerun claim과 맞습니다.
- 이번 라운드 범위는 current MVP 안에 머물렀습니다.
  - search-only preview-card의 second-card content-match tooltip regression 1건만 다뤘고 approval/storage/session schema, web investigation, reviewed-memory, watcher 쪽으로 넓어지지 않았습니다.
- 다만 latest `/work`의 "same-family current-risk 닫힘" 결론은 현재 shipped contract 전체 기준으로는 아직 완전히 닫히지 않았습니다.
  - root docs는 document search responses가 `both search-only and search-plus-summary`에서 structured search result preview panel을 포함한다고 적습니다.
  - 구현도 transcript renderer에서는 `Array.isArray(message.search_results)`면 항상 `.search-preview-panel`과 각 card(filename, tooltip, badge, snippet)를 렌더링합니다.
  - 하지만 current browser smoke의 folder-search(search-plus-summary) 시나리오는 quick-meta/transcript meta와 `selected-text`만 확인하고, transcript preview panel 자체는 직접 잠그지 않습니다.
- 따라서 다음 exact slice는 same-family current-risk인 `document-search search-plus-summary transcript preview-card regression coverage` 1건이 맞습니다.

## 검증
- `sed -n '1,220p' work/4/3/2026-04-03-document-search-preview-card-content-match-tooltip-regression-coverage.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-content-match-snippet-regression-coverage-verification.md`
- `sed -n '1,260p' .pipeline/codex_feedback.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '214,250p'`
  - second card `memo.md` + tooltip + `내용 일치` + snippet assertion이 search-only 시나리오에 존재함을 확인
- `sed -n '180,205p' e2e/tests/web-smoke.spec.mjs`
  - folder-search(search-plus-summary) 시나리오는 현재 preview panel 자체를 직접 확인하지 않음을 확인
- `sed -n '126,134p' docs/PRODUCT_SPEC.md`
- `sed -n '28,31p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '26,31p' README.md`
  - both search-only and search-plus-summary preview-panel contract 문서화 확인
- `nl -ba app/static/app.js | sed -n '998,1032p'`
  - transcript renderer가 `search_results`가 있으면 항상 `.search-preview-panel`을 append함을 확인
- `make e2e-test`
  - `17 passed (2.1m)`
- 미실행:
  - `python3 -m unittest -v tests.test_web_app`
  - 이번 latest `/work`는 Playwright assertion 1건 범위였고 Python/server 로직 변경이 없어 browser rerun만 다시 실행했습니다.

## 남은 리스크
- latest `/work`의 second-card content-match tooltip assertion과 browser rerun claim은 truthful합니다.
- 하지만 current shipped docs가 약속한 search-plus-summary preview panel은 browser smoke에서 아직 direct regression coverage가 없습니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `document-search search-plus-summary transcript preview-card regression coverage` 1건으로 갱신했습니다.
