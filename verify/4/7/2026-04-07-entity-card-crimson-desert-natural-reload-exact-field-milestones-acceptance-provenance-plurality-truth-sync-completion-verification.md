# entity-card crimson-desert natural-reload exact-field milestones-acceptance provenance-plurality truth-sync completion verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-milestones-acceptance-provenance-plurality-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `docs/MILESTONES.md:70`, `docs/ACCEPTANCE_CRITERIA.md:1361`의 crimson-desert natural-reload exact-field line에서 context box provenance plurality drift를 닫았다고 주장하므로, current truth와 재대조가 필요했습니다.
- rerun 결과 `README.md:152`, `docs/TASK_BACKLOG.md:59`, `docs/NEXT_STEPS.md:16`, `e2e/tests/web-smoke.spec.mjs:4242`가 가리키는 exact-field truth와 latest `/work`의 docs 수정 범위가 일치했습니다.
- same-axis 다음 current-risk는 `docs/NEXT_STEPS.md:16`의 `entity-card 붉은사막 browser natural-reload follow-up/second-follow-up` clause가 actual-search follow-up/second-follow-up truth에 없는 `blog.example.com` provenance를 아직 직접 붙여 두는 giant-summary overstatement였습니다.

## 핵심 변경
- latest `/work`가 truthful함을 확인하고, 검증 결과를 persistent `/verify` note로 남겼습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert docs-next-steps follow-up-second-follow-up provenance-overstatement correction`으로 고정했습니다.

## 검증
- `sed -n '1,240p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-milestones-acceptance-provenance-plurality-truth-sync-completion.md`
- `sed -n '1,240p' verify/4/7/2026-04-07-entity-card-zero-strong-slot-click-reload-second-follow-up-milestones-web-badge-truth-sync-completion-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba docs/MILESTONES.md | sed -n '70,77p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1368p'`
- `nl -ba README.md | sed -n '152,159p'`
- `git diff --check -- docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "entity-card 붉은사막 검색 결과|source path plurality|blog\\.example\\.com|namu\\.wiki|ko\\.wikipedia\\.org" docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md e2e/tests/web-smoke.spec.mjs`
- `rg -n "붉은사막 자연어 reload 후 follow-up|붉은사막 자연어 reload 후 두 번째 follow-up|blog\\.example\\.com" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/ACCEPTANCE_CRITERIA.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4870,5075p'`
- `nl -ba tests/test_web_app.py | sed -n '16443,16635p'`
- `nl -ba README.md | sed -n '157,165p'`
- `nl -ba docs/MILESTONES.md | sed -n '75,83p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1366,1374p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '64,72p'`
- `sed -n '1,240p' work/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-family-closure-provenance-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-family-closure-provenance-truth-sync-completion-verification.md`
- `rg -n "붉은사막 browser natural-reload follow-up/second-follow-up|noisy single-source claim|blog\\.example\\.com provenance" docs/NEXT_STEPS.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `git diff --check -- docs/NEXT_STEPS.md`
- `git diff --check -- verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-milestones-acceptance-provenance-plurality-truth-sync-completion-verification.md .pipeline/claude_handoff.md`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/NEXT_STEPS.md:16`의 `entity-card 붉은사막 browser natural-reload follow-up/second-follow-up` clause는 `README.md:157`, `README.md:159`, `README.md:165`, `docs/MILESTONES.md:75`, `docs/MILESTONES.md:77`, `docs/MILESTONES.md:83`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/ACCEPTANCE_CRITERIA.md:1374`, `docs/TASK_BACKLOG.md:64`, `docs/TASK_BACKLOG.md:66`, `docs/TASK_BACKLOG.md:72`, `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:5045`, `tests/test_web_app.py:16443`, `tests/test_web_app.py:16582`가 가리키는 actual-search follow-up/second-follow-up truth보다 강했습니다. current shipped truth는 `namu.wiki`, `ko.wikipedia.org` continuity와 response-origin drift prevention까지이고, `blog.example.com` provenance는 noisy-single-source family에만 직접 남아야 합니다.
