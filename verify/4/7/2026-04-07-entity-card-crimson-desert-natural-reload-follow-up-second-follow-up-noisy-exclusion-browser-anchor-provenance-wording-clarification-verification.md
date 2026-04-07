# entity-card crimson-desert natural-reload follow-up-second-follow-up noisy-exclusion browser-anchor provenance wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-browser-anchor-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload noisy-exclusion browser anchors의 title/session naming을 provenance contract까지 드러내도록 정리했다고 보고했습니다. 이번 라운드에서는 그 code change 자체와 claimed verification, 그리고 `남은 리스크 없음` 서술이 현재 tree와 모두 맞는지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`가 직전 actual-search second-follow-up naming round를 닫았으므로, 이번 라운드에서는 noisy-exclusion branch까지 이어진 browser naming chain이 truthfully 닫혔는지도 같이 확인해야 했습니다.

## 핵심 변경
- latest `/work`는 부분만 truthful했습니다. code change 자체는 맞았습니다. `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5108`, `e2e/tests/web-smoke.spec.mjs:5186`, `e2e/tests/web-smoke.spec.mjs:5187`에서 natural-reload follow-up/second-follow-up noisy-exclusion titles와 session ids가 now negative `출시일/2025/blog.example.com` assertion과 `blog.example.com provenance`를 직접 드러냅니다.
- 다만 `/work`의 검증 문구는 과장입니다. note에 적힌 exact rerun `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "noisy single-source claim" --reporter=line`를 다시 돌리면 current tree에서는 `7 passed (42.0s)`가 나옵니다. 따라서 `/work`의 `2 passed`는 exact command truth와 맞지 않습니다.
- `남은 리스크 없음`도 과장입니다. generic noisy-single-source natural-reload browser anchors `e2e/tests/web-smoke.spec.mjs:6242`, `e2e/tests/web-smoke.spec.mjs:6243`, `e2e/tests/web-smoke.spec.mjs:6315`, `e2e/tests/web-smoke.spec.mjs:6316`은 still provenance/negative-assertion contract를 title/session naming에서 직접 드러내지 않습니다.
- 다음 Claude 슬라이스는 `entity-card noisy-single-source natural-reload follow-up-second-follow-up browser-anchor provenance wording clarification`으로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-browser-anchor-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-second-follow-up-browser-anchor-naming-clarification-verification.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5106,5268p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6238,6472p'`
- `nl -ba README.md | sed -n '182,188p'`
- `nl -ba docs/MILESTONES.md | sed -n '95,98p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1397p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,95p'`
- `nl -ba tests/test_web_app.py | sed -n '17272,17508p'`
- `rg -n '^test\\(\".*noisy single-source claim' e2e/tests/web-smoke.spec.mjs`
- `rg -n "noisy single-source claim|entity-crimson-natural-reload-(followup|second-followup)-noisy-excl|entity-noisy-click-(fu|2fu)|blog.example.com provenance|출시일|2025" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "noisy single-source claim" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 narrow browser-title verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 generic noisy-single-source natural-reload browser anchor wording weakness입니다. `README.md:184`, `README.md:185`, `docs/ACCEPTANCE_CRITERIA.md:1393`, `docs/ACCEPTANCE_CRITERIA.md:1394`, `docs/TASK_BACKLOG.md:91`, `docs/TASK_BACKLOG.md:92`, `tests/test_web_app.py:17275`, `tests/test_web_app.py:17332`는 follow-up/second-follow-up natural-reload에서 negative `출시일`/`2025`/`blog.example.com` assertions와 `blog.example.com` provenance continuity를 직접 적습니다.
- 반면 `e2e/tests/web-smoke.spec.mjs:6242`, `e2e/tests/web-smoke.spec.mjs:6243`, `e2e/tests/web-smoke.spec.mjs:6315`, `e2e/tests/web-smoke.spec.mjs:6316`은 still `다시 노출되지 않습니다`와 generic session naming만 남아 있어, already-tested provenance contract가 browser anchor title/session naming에서 직접 드러나지 않습니다. 다음 라운드는 runtime/assertion logic과 docs를 건드리지 않는 test-only wording clarification이 가장 작고 reviewable합니다.
