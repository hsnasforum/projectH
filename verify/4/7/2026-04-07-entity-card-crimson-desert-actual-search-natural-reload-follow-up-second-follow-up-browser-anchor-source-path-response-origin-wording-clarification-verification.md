# entity-card crimson-desert actual-search natural-reload follow-up/second-follow-up browser-anchor source-path-response-origin wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-actual-search-natural-reload-follow-up-second-follow-up-browser-anchor-source-path-response-origin-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card 붉은사막 actual-search natural-reload follow-up/second-follow-up browser anchor title wording이 source-path plurality와 response-origin continuity truth를 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 test-only wording change, claimed rerun, 그리고 family closure 서술이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`가 source-path-only initial natural-reload anchor까지는 already 좁혀 두었으므로, 이번에는 actual-search follow-up/second-follow-up browser anchor wording이 닫혔는지와 다음 same-family current-risk가 어디에 남는지 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`는 부분만 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:4990`, `e2e/tests/web-smoke.spec.mjs:5045`의 title wording 보정은 current tree와 일치하고, `/work`가 적은 `session ID 변경 없음`도 `e2e/tests/web-smoke.spec.mjs:4871`, `e2e/tests/web-smoke.spec.mjs:4991`, `e2e/tests/web-smoke.spec.mjs:5046` 기준으로 맞았습니다.
- `/work`가 적은 exact rerun도 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후" --reporter=line`은 `3 passed (18.6s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- 다만 `/work`의 `붉은사막 natural-reload family browser anchor wording clarification 전체 완료`는 과장입니다. root docs인 `README.md:166`, `README.md:167`, `docs/MILESTONES.md:78`, `docs/MILESTONES.md:79`, `docs/ACCEPTANCE_CRITERIA.md:1369`, `docs/ACCEPTANCE_CRITERIA.md:1370`, `docs/TASK_BACKLOG.md:67`, `docs/TASK_BACKLOG.md:68`과 same test bodies `e2e/tests/web-smoke.spec.mjs:5156`, `e2e/tests/web-smoke.spec.mjs:5162`, `e2e/tests/web-smoke.spec.mjs:5179`, `e2e/tests/web-smoke.spec.mjs:5180`, `e2e/tests/web-smoke.spec.mjs:5237`, `e2e/tests/web-smoke.spec.mjs:5244`, `e2e/tests/web-smoke.spec.mjs:5261`, `e2e/tests/web-smoke.spec.mjs:5262`는 noisy-exclusion follow-up/second-follow-up에서 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` continuity를 함께 가리킵니다.
- 반면 browser anchors `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5186`과 session naming `e2e/tests/web-smoke.spec.mjs:5108`, `e2e/tests/web-smoke.spec.mjs:5187`은 still noisy single-source claim exclusion과 `blog.example.com` provenance continuity만 title/session wording에 드러내고, agreement continuity와 wiki source-path continuity는 직접 적지 않습니다.
- 다음 Claude 슬라이스는 `entity-card crimson-desert natural-reload follow-up-second-follow-up noisy-exclusion browser-anchor continuity wording clarification`으로 고정했습니다. runtime/assertion logic과 docs를 건드리지 않고 `e2e/tests/web-smoke.spec.mjs` follow-up/second-follow-up noisy-exclusion browser anchor wording만 body truth에 맞추는 test-only clarification이 same-family smallest current-risk reduction입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-actual-search-natural-reload-follow-up-second-follow-up-browser-anchor-source-path-response-origin-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-source-path-browser-anchor-provenance-wording-clarification-verification.md`
- `sed -n '4866,5106p' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5104,5265p'`
- `nl -ba README.md | sed -n '156,170p'`
- `nl -ba docs/MILESTONES.md | sed -n '74,86p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1365,1378p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '63,75p'`
- `nl -ba tests/test_web_app.py | sed -n '16436,17340p'`
- `rg -n "entity-card 붉은사막 actual-search 자연어 reload 후|entity-card 붉은사막 자연어 reload 후|entity-actual-search-natural-reload|noisy single-source claim|설명형 다중 출처 합의|백과 기반" e2e/tests/web-smoke.spec.mjs | sed -n '1,120p'`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 actual-search 자연어 reload 후" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후 .*noisy single-source claim" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- same-family smallest current-risk는 entity-card 붉은사막 natural-reload follow-up/second-follow-up noisy-exclusion browser anchor wording weakness입니다. `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5186`의 title/session naming이 body가 이미 검사하는 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` continuity를 직접 드러내지 않습니다.
- 다음 라운드는 `e2e/tests/web-smoke.spec.mjs`의 noisy-exclusion follow-up/second-follow-up browser anchors만 다루는 test-only wording clarification으로 충분합니다. actual-search source-path/response-origin anchors, source-path-only initial anchor, click-reload family, docs, service tests는 범위 밖입니다.
