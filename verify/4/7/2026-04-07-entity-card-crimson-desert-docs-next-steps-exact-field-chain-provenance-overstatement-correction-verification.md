# entity-card crimson-desert docs-next-steps exact-field chain-provenance overstatement correction verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-exact-field-chain-provenance-overstatement-correction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `docs/NEXT_STEPS.md:16`의 crimson-desert exact-field clause 끝에서 follow-up/second-follow-up chain provenance wording을 제거해, initial exact-field와 later continuity clause를 분리했다고 주장하므로 현재 tree와 root/staged docs를 다시 맞춰 볼 필요가 있었습니다.
- rerun 결과 `docs/NEXT_STEPS.md:16`의 `entity-card 붉은사막 검색 결과 browser natural-reload exact-field + noisy exclusion` clause는 now initial natural-reload exact-field truth만 가리키고, `README.md:152`, `README.md:158`, `docs/MILESTONES.md:70`, `docs/MILESTONES.md:76`, `docs/ACCEPTANCE_CRITERIA.md:1361`, `docs/ACCEPTANCE_CRITERIA.md:1367`, `docs/TASK_BACKLOG.md:59`가 적는 exact-field wording과 맞습니다.
- same-family 다음 current-risk는 actual-search crimson natural-reload follow-up/second-follow-up path에서 noisy exclusion이 explicit contract로 잠겨 있지 않다는 점입니다. current browser/service/docs는 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` continuity만 직접 잠그고 있고, `출시일`, `2025`, `blog.example.com` 미노출은 initial exact-field에만 explicit합니다. 이 마지막 판단은 current coverage gap에 대한 추론입니다.

## 핵심 변경
- latest `/work`가 truthful함을 확인하고, crimson-desert exact-field chain-provenance overstatement correction이 current docs truth와 맞음을 persistent `/verify` note로 남겼습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload follow-up-second-follow-up noisy-exclusion tightening`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `ls -1t verify/4/7 | head -n 8`
- `sed -n '1,240p' work/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-exact-field-chain-provenance-overstatement-correction.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-docs-next-steps-follow-up-second-follow-up-exact-negative-anchor-truth-sync-completion-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba README.md | sed -n '152,165p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,83p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1374p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,72p'`
- `nl -ba tests/test_web_app.py | sed -n '16390,16620p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4242,5065p'`
- `git diff --check -- docs/NEXT_STEPS.md`
- `rg -n "entity-card 붉은사막 검색 결과|entity-card 붉은사막 browser natural-reload follow-up/second-follow-up|blog\\.example\\.com|namu\\.wiki|ko\\.wikipedia\\.org|출시일|2025" docs/NEXT_STEPS.md README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `rg -n "actual.*noisy exclusion|붉은사막.*noisy exclusion|actual entity search.*출시일|actual entity search.*blog\\.example\\.com|crimson-desert.*follow-up.*출시일|crimson-desert.*follow-up.*blog\\.example\\.com" work/4/7 verify/4/7 tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
- `git status --short`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- actual-search crimson natural-reload family에서 explicit noisy exclusion contract는 initial exact-field에만 직접 잠겨 있습니다. browser initial exact-field는 `e2e/tests/web-smoke.spec.mjs:4242`와 `e2e/tests/web-smoke.spec.mjs:4314`에서 `출시일`, `2025`, `blog.example.com` 미노출과 provenance를 함께 확인하지만, follow-up/second-follow-up browser scenarios인 `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:4990`, `e2e/tests/web-smoke.spec.mjs:5045`는 2-source fixture로 source-path/response-origin continuity만 잠급니다.
- service 쪽도 `tests/test_web_app.py:16443`, `tests/test_web_app.py:16511`, `tests/test_web_app.py:16582`는 actual-search natural-reload follow-up/second-follow-up continuity만 잠그고, noisy 3-source record에서 `출시일`, `2025`, `blog.example.com`이 계속 미노출되는지는 직접 확인하지 않습니다.
- 대응 docs인 `README.md:157`, `README.md:159`, `README.md:165`, `docs/MILESTONES.md:75`, `docs/MILESTONES.md:77`, `docs/MILESTONES.md:83`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/ACCEPTANCE_CRITERIA.md:1374`, `docs/TASK_BACKLOG.md:64`, `docs/TASK_BACKLOG.md:66`, `docs/TASK_BACKLOG.md:72`도 same flow를 continuity로만 적고 있습니다. 이 coverage gap은 current user-visible flow risk에 가깝고, 다음 라운드에서 service/browser tightening과 docs truth-sync를 함께 다루는 편이 가장 자연스럽습니다.
