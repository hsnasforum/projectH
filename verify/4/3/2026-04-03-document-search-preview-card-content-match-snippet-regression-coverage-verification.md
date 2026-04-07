## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-content-match-snippet-regression-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-content-match-snippet-regression-coverage.md`가 직전 `/verify`가 넘긴 content-match snippet current-risk를 실제로 닫았는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-content-match-badge-regression-coverage-verification.md`가 다음 exact slice로 잡았던 `document-search preview-card content-match snippet regression coverage`가 current tree와 rerun 결과에 truthful한지도 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 코드 변경과 browser rerun 주장은 대부분 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 search-only 시나리오에는 실제로 response detail/transcript 양쪽 second card에 대해 `.search-preview-snippet` visible과 `"budget"` 텍스트 포함 assertion이 추가되어 있습니다.
  - 재실행한 `make e2e-test`도 `17 passed (2.1m)`로 통과해 latest `/work`의 rerun claim과 맞습니다.
- 이번 라운드 범위는 current MVP 안에 머물렀습니다.
  - search-only preview-card의 second-card content-match snippet regression 1건만 다뤘고 approval/storage/session schema, web investigation, reviewed-memory, watcher 쪽으로 넓어지지 않았습니다.
- 다만 latest `/work`의 "preview-card contract(filename, tooltip, badge 양쪽, snippet 양쪽)의 code/regression/docs가 모두 정합" 결론은 아직 완전히 닫히지 않았습니다.
  - 현재 smoke는 first card의 full-path tooltip만 직접 확인하고 있습니다.
  - second card는 filename, `내용 일치` badge, snippet visibility/text까지는 이번 latest tree에서 잠겼지만, full-path tooltip은 아직 직접 잠그지 않습니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 각 preview card가 matched file name with full path tooltip을 보여 준다고 적고, 구현도 transcript/response preview renderer 양쪽에서 모든 card에 `nameEl.title = sr.path || ""`를 설정합니다.
- 따라서 다음 exact slice는 same-family current-risk인 `document-search preview-card content-match tooltip regression coverage` 1건이 맞습니다.

## 검증
- `sed -n '1,120p' work/4/3/2026-04-03-document-search-preview-card-content-match-snippet-regression-coverage.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-document-search-preview-card-content-match-badge-regression-coverage-verification.md`
- `sed -n '1,260p' .pipeline/codex_feedback.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '214,248p'`
  - second card `memo.md` + `내용 일치` + snippet visibility/text assertion 추가 확인
- `rg -n "title\\)|toHaveAttribute\\(\\\"title\\\"|memo\\.md|budget-plan\\.md" e2e/tests/web-smoke.spec.mjs`
  - `title` assertion은 여전히 first card 2건만 존재
- `sed -n '26,31p' README.md`
- `sed -n '28,31p' docs/ACCEPTANCE_CRITERIA.md`
- `sed -n '130,133p' docs/PRODUCT_SPEC.md`
  - preview card contract가 각 matched file name의 full-path tooltip을 문서화하고 있음을 재확인
- `make e2e-test`
  - `17 passed (2.1m)`
- 미실행:
  - `python3 -m unittest -v tests.test_web_app`
  - 이번 latest `/work`는 Playwright assertion 1건 범위였고 Python/server 로직 변경이 없어 browser rerun만 다시 실행했습니다.

## 남은 리스크
- latest `/work`의 second-card snippet assertion과 browser rerun claim은 truthful합니다.
- 하지만 content-match branch의 full-path tooltip은 아직 direct regression coverage가 없습니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `document-search preview-card content-match tooltip regression coverage` 1건으로 갱신했습니다.
