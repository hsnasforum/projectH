## 변경 파일
- `verify/4/3/2026-04-03-document-search-search-plus-summary-transcript-preview-card-regression-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-search-plus-summary-transcript-preview-card-regression-coverage.md`가 직전 `/verify`가 넘긴 same-family current-risk를 실제로 닫았는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-document-search-preview-card-content-match-tooltip-regression-coverage-verification.md`가 다음 exact slice로 잡았던 `document-search search-plus-summary transcript preview-card regression coverage`가 current tree와 rerun 결과에 truthful한지도 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 Playwright assertion 추가와 browser rerun claim은 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 folder-search(search-plus-summary) 시나리오에는 실제로 transcript last assistant의 `.search-preview-panel` visible, `.search-preview-item` count 2, first card filename(`budget-plan.md`), first card badge(`파일명 일치`) assertion이 추가되어 있습니다.
  - 재실행한 `make e2e-test`도 `17 passed (2.1m)`로 통과해 latest `/work`의 rerun claim과 맞습니다.
- 이번 라운드 범위는 current MVP 안에 머물렀습니다.
  - document-search browser smoke의 folder-search transcript preview-panel regression 1건만 다뤘고 production behavior, approval/storage/session schema, web investigation, reviewed-memory, watcher 쪽으로 넓어지지 않았습니다.
- 다만 latest `/work`의 "docs는 이미 기술되어 추가 동기화 불필요" 및 "same-family current-risk 닫힘" 결론은 현재 smoke-coverage 문서 기준으로는 과장입니다.
  - product behavior 계약 자체는 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에 이미 both-path preview panel로 적혀 있습니다.
  - 하지만 smoke coverage 요약은 아직 stale합니다. `README.md`의 scenario 3, `docs/ACCEPTANCE_CRITERIA.md`의 Playwright gate bullet, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 여전히 folder-search scenario를 `선택 결과 요약` source-type label과 `출처 2개` metadata까지만 적고, 이번 round에서 실제 추가된 transcript preview-panel regression coverage를 반영하지 않습니다.
- 따라서 이번 family의 다음 exact slice는 `playwright search-plus-summary transcript preview-card docs truth-sync` 1건이 맞습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/3/2026-04-03-document-search-search-plus-summary-transcript-preview-card-regression-coverage.md`
- `sed -n '1,240p' verify/4/3/2026-04-03-document-search-preview-card-content-match-tooltip-regression-coverage-verification.md`
- `sed -n '1,220p' .pipeline/codex_feedback.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '176,230p'`
- `nl -ba README.md | sed -n '24,92p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '126,138p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '26,38p;1312,1326p'`
- `nl -ba docs/MILESTONES.md | sed -n '32,42p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '19,29p'`
- `nl -ba app/static/app.js | sed -n '998,1034p;1178,1210p'`
- `rg -n "browser folder picker search flow|folder-search scenario now also covers|browser folder picker with|search-preview-panel|search-preview-item|search-preview-name|search-preview-match" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md e2e/tests/web-smoke.spec.mjs`
  - scenario 3 docs summary는 여전히 metadata까지만 적고, current Playwright는 preview-panel assertion까지 포함함을 확인
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
  - 통과
- `make e2e-test`
  - `17 passed (2.1m)`
- 미실행:
  - `python3 -m unittest -v tests.test_web_app`
  - 이번 latest `/work`는 Playwright assertion 1건 범위였고 Python/server 로직 변경이 없어 browser rerun만 다시 실행했습니다.

## 남은 리스크
- current tree의 folder-search transcript preview-panel assertion과 browser rerun claim은 truthful합니다.
- 하지만 smoke-coverage docs가 아직 이번 assertion 확대를 반영하지 않아 `/work`의 docs-sync 불필요 판단은 현재 truth와 맞지 않습니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `playwright search-plus-summary transcript preview-card docs truth-sync` 1건으로 갱신했습니다.
