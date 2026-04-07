## 변경 파일
- `verify/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-panel-visibility-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-panel-visibility.md`가 직전 same-day `/verify`가 넘긴 same-family user-visible slice를 실제로 truthful하게 구현했는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-playwright-search-plus-summary-transcript-preview-card-both-card-coverage-docs-truth-sync-verification.md`가 다음 exact slice로 지정했던 `document-search search-plus-summary response-detail preview-panel visibility`가 current tree와 rerun 결과에 맞는지도 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 코드 변경 존재와 rerun claim 자체는 맞습니다.
  - `app/static/app.js`에는 `hasResults` 분기 추가가 실제로 들어가 있어 `search_results`가 있으면 `#response-search-preview`를 보이게 하려는 변경이 존재합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 folder-search scenario에는 `response-search-preview` visible, item count 2, `response-text` visible assertion이 실제로 추가되어 있습니다.
  - 재실행한 `make e2e-test`는 `17 passed (2.3m)`, `python3 -m unittest -v tests.test_web_app`는 `Ran 187 tests in 31.599s`, `OK`였습니다.
- 다만 latest `/work`의 `search-plus-summary -> preview panel + body text 둘 다 보임` 결론은 현재 코드만 보면 과장입니다.
  - [app/static/app.js](/home/xpdlqj/code/projectH/app/static/app.js#L1179)에서 `hasResults` 분기로 바뀌었지만, [app/static/app.js](/home/xpdlqj/code/projectH/app/static/app.js#L1183)에서 `search-only`일 때만 `responseText.hidden = true`를 설정하고, [app/static/app.js](/home/xpdlqj/code/projectH/app/static/app.js#L1210) 이하의 `responseText.hidden = false` 복구는 `hasResults == false`일 때만 실행됩니다.
  - 따라서 `search-only` 응답이 먼저 body를 숨긴 뒤 같은 페이지에서 `search-plus-summary` 응답이 오면, preview panel은 보이더라도 body hidden state가 그대로 남습니다. 이는 source inspection에 근거한 추론입니다.
  - current Playwright는 fresh session의 folder-search happy path만 확인하므로 이 상태 전이 회귀를 잡지 못합니다.
- docs truth-sync도 이번 `/work`에서는 닫히지 않았습니다.
  - browser-visible smoke contract가 folder-search scenario에서 response detail preview visibility까지 넓어졌지만, [README.md](/home/xpdlqj/code/projectH/README.md#L84), [docs/ACCEPTANCE_CRITERIA.md](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1318), [docs/MILESTONES.md](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L36), [docs/TASK_BACKLOG.md](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L23)는 여전히 transcript preview panel 중심 wording만 유지합니다.
- 이번 라운드 범위 자체는 current MVP 안에 머물렀습니다.
  - document-search response-detail preview surface 1건만 다뤘고 approval/storage/session schema, web investigation, reviewed-memory, watcher 쪽으로 넓어지지 않았습니다.
- 따라서 다음 exact slice는 same-family current-risk reduction 1건이 우선입니다.
  - `renderResponseSearchPreview()`가 `search-only -> search-plus-summary` 전환에서 `response-text` hidden state를 복구하도록 고치고, 그 전환을 직접 잠그는 browser regression 1건을 추가하는 편이 가장 좁고 실제 리스크를 바로 줄입니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `git status --short`
- `ls -lt work/4/3/*.md | head -n 8`
- `ls -lt verify/4/3/*.md | head -n 10`
- `sed -n '1,260p' .pipeline/codex_feedback.md`
- `sed -n '1,260p' work/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-panel-visibility.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-playwright-search-plus-summary-transcript-preview-card-both-card-coverage-docs-truth-sync-verification.md`
- `nl -ba app/static/app.js | sed -n '1177,1215p;3144,3154p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '182,245p'`
- `nl -ba README.md | sed -n '24,90p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '130,136p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '28,31p;1315,1320p'`
- `git show --stat --summary HEAD -- app/static/app.js e2e/tests/web-smoke.spec.mjs work/4/3/2026-04-03-document-search-search-plus-summary-response-detail-preview-panel-visibility.md`
  - current commit 범위가 `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, `/work` 메모 1개인지 확인했습니다.
- `git diff --unified=5 HEAD^..HEAD -- app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - `hasResults` 분기 추가와 folder-search response-detail assertions 추가만 들어갔는지 확인했습니다.
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - 통과
- `rg -n "responseText\\.hidden = false|responseText\\.hidden = true|response-search-preview|response-text" app/static/app.js e2e/tests/web-smoke.spec.mjs`
  - hidden-state reset이 `hasResults == false` 분기에만 있는지, 새 Playwright assertion 위치가 어디인지 확인했습니다.
- `rg -n "response detail|response-search-preview|summary body|search-plus-summary" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md -S`
  - root docs general contract와 smoke coverage wording이 어디까지 반영됐는지 확인했습니다.
- `python3 -m unittest -v tests.test_web_app`
  - `Ran 187 tests in 31.599s`
  - `OK`
- `make e2e-test`
  - `17 passed (2.3m)`

## 남은 리스크
- latest `/work`의 rerun claim은 truthful하지만, current code는 `search-only -> search-plus-summary` 전환에서 `response-text` hidden state를 복구하지 못해 latest `/work`의 body-visible 결론을 완전히 뒷받침하지 못합니다.
- smoke coverage docs 4곳도 이번 round의 response-detail visibility assertion 확대를 아직 반영하지 않았습니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `document-search response-detail body-visibility reset after search-only` 1건으로 갱신했습니다.
