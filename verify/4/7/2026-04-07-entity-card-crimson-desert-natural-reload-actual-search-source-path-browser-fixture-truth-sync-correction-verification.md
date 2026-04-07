# entity-card crimson-desert natural-reload actual-search source-path browser-fixture truth-sync correction verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-source-path-browser-fixture-truth-sync-correction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson natural-reload actual-search source-path browser fixture의 truth-sync correction이 끝났다고 보고했습니다. 이번 라운드에서는 그 주장 자체가 현재 tree와 맞는지, 그리고 같은 family에서 다음 한 슬라이스를 어디까지 좁힐 수 있는지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 이전 browser-anchor naming round만 다뤘기 때문에, 이번 `/work`가 닫은 범위와 현재 남은 same-family current-risk를 새로 재대조해야 했습니다.

## 핵심 변경
- latest `/work`를 truthful로 판정했습니다. `e2e/tests/web-smoke.spec.mjs`의 actual-search follow-up source-path browser fixture comment와 seeded `verification_label`/history metadata가 now `설명형 다중 출처 합의`로 맞춰져 있었고, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과도 `75`로 유지됐습니다.
- claimed scenario보다 넓게 `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후" --reporter=line`를 다시 돌렸고 `3 passed`를 확인했습니다. 따라서 latest `/work`가 말한 targeted browser correction은 actual-search browser family 안에서 그대로 유지되고 있습니다.
- 다음 Claude 슬라이스는 `entity-card crimson-desert natural-reload actual-search second-follow-up source-path-response-origin browser-anchor naming clarification`으로 고정했습니다. root docs와 service anchor는 second-follow-up actual-search를 source path + response-origin continuity로 직접 적는데, browser smoke title/session naming은 아직 response-origin만 드러내고 있어 같은 family에서 가장 작은 current-risk가 남아 있습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-source-path-browser-fixture-truth-sync-correction.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-actual-search-browser-anchor-naming-clarification-verification.md`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4868,5208p'`
- `nl -ba tests/test_web_app.py | sed -n '16498,16605p'`
- `nl -ba tests/test_web_app.py | sed -n '17310,17515p'`
- `nl -ba README.md | sed -n '156,166p'`
- `nl -ba docs/MILESTONES.md | sed -n '76,86p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1367,1378p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '65,75p'`
- `rg -n '설명형 단일 출처|설명형 다중 출처 합의|actual-search|entity-actual-search-natural-reload' e2e/tests/web-smoke.spec.mjs tests/test_web_app.py`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 좁은 browser-fixture verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 second-follow-up actual-search browser anchor naming ambiguity입니다. `README.md:165`, `docs/MILESTONES.md:85`, `docs/ACCEPTANCE_CRITERIA.md:1376`, `docs/TASK_BACKLOG.md:74`, `tests/test_web_app.py:16582`는 모두 source path + response-origin continuity를 직접 적는데, `e2e/tests/web-smoke.spec.mjs:5045`와 `e2e/tests/web-smoke.spec.mjs:5046`은 still response-origin 중심 naming만 노출합니다.
- browser body 자체는 이미 `e2e/tests/web-smoke.spec.mjs:5100-5102`에서 `namu.wiki`, `ko.wikipedia.org` context box continuity를 확인하므로 runtime risk는 보이지 않았습니다. 다음 라운드는 runtime/assertion logic이나 docs를 건드리지 말고 이 second-follow-up browser anchor naming만 정리하는 test-only slice가 가장 작고 reviewable합니다.
