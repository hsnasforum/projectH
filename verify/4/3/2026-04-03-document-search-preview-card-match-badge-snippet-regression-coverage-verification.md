## 변경 파일
- `verify/4/3/2026-04-03-document-search-preview-card-match-badge-snippet-regression-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/3/2026-04-03-document-search-preview-card-match-badge-snippet-regression-coverage.md`가 직전 `/verify`가 넘긴 preview-card badge/snippet current-risk를 실제로 닫았는지 다시 확인해야 했습니다.
- 같은 날 최신 기존 `/verify`인 `verify/4/3/2026-04-03-playwright-preview-card-tooltip-docs-truth-sync-verification.md`가 다음 exact slice로 잡았던 `document-search preview-card match-badge-snippet regression coverage`가 current tree와 rerun 결과에 truthful한지도 재대조해야 했습니다.

## 핵심 변경
- latest `/work`의 코드 변경과 browser rerun 주장은 대부분 truthful합니다.
  - `e2e/tests/web-smoke.spec.mjs`의 search-only 시나리오에는 실제로 response detail/transcript 양쪽 첫 card에 대해 `.search-preview-match`가 `"파일명 일치"`를 포함하는지, `.search-preview-snippet`이 보이는지 확인하는 assertion이 추가되어 있습니다.
  - 재실행한 `make e2e-test`도 `17 passed (2.1m)`로 통과해 latest `/work`의 rerun claim과 맞습니다.
- 이번 라운드 범위는 current MVP 안에 머물렀습니다.
  - preview-card badge/snippet regression coverage와 그에 맞춘 smoke coverage wording만 다뤘고 approval/storage/session schema, web investigation, reviewed-memory, watcher로 넓어지지 않았습니다.
- 다만 latest `/work`의 "preview-card contract(filename, tooltip, badge, snippet)의 code/regression/docs가 모두 정합" 결론은 아직 완전히 닫히지 않았습니다.
  - latest `/work`와 root docs 4개는 smoke scenario 4가 match-type badge `파일명 일치 / 내용 일치` plus snippet visibility를 덮는다고 적습니다.
  - 하지만 실제 Playwright assertion은 response detail/transcript 양쪽 모두 첫 card의 `.search-preview-match`가 `"파일명 일치"`인지 확인할 뿐이며, `내용 일치` badge path는 직접 잠그지 않습니다.
  - 현재 fixture/query 조합에서는 `budget-plan.md`가 filename match, `memo.md`가 content match가 되도록 구현되어 있으므로, `내용 일치` branch는 shipped contract이면서도 direct regression coverage가 남아 있습니다.
- 따라서 다음 exact slice는 same-family current-risk인 `document-search preview-card content-match badge regression coverage` 1건이 맞습니다.

## 검증
- `sed -n '1,120p' work/4/3/2026-04-03-document-search-preview-card-match-badge-snippet-regression-coverage.md`
- `sed -n '1,260p' verify/4/3/2026-04-03-playwright-preview-card-tooltip-docs-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/codex_feedback.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 통과
- `rg -n "search-preview-match|파일명 일치|내용 일치|search-preview-snippet|memo\\.md" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/3/2026-04-03-document-search-preview-card-match-badge-snippet-regression-coverage.md`
  - docs와 `/work`는 `파일명 일치 / 내용 일치` 모두를 언급
  - actual Playwright assertion은 `.search-preview-match`.first()의 `"파일명 일치"`만 확인
- `nl -ba core/agent_loop.py | sed -n '760,782p'`
  - filename match는 `matched_on="filename"`, 본문 match는 `matched_on="content"`로 분기됨을 확인
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '212,242p'`
  - current smoke가 first card만 확인하고 second card의 `내용 일치` branch는 직접 잠그지 않음을 확인
- `make e2e-test`
  - `17 passed (2.1m)`
- 미실행:
  - `python3 -m unittest -v tests.test_web_app`
  - 이번 latest `/work`는 Playwright assertion + docs wording 범위였고 Python/server 로직 변경이 없으므로 browser rerun만 다시 실행했습니다.

## 남은 리스크
- latest `/work`의 first-card badge/snippet assertion 추가와 browser rerun claim은 truthful하지만, `내용 일치` badge path는 아직 direct regression coverage가 없습니다.
- 현재 docs와 `/work`가 smoke coverage를 `파일명 일치 / 내용 일치` 전체로 읽히게 적고 있어, coverage 설명이 실제 assertion 범위를 약간 넘깁니다.
- 따라서 `.pipeline/codex_feedback.md`는 `STATUS: implement`를 유지하되, 다음 exact slice를 `document-search preview-card content-match badge regression coverage` 1건으로 갱신했습니다.
