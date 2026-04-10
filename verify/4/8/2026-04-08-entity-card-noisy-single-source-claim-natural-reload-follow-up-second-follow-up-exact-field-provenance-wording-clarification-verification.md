# entity-card noisy single-source claim natural-reload follow-up + second-follow-up exact-field provenance wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-follow-up-second-follow-up-exact-field-provenance-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card noisy single-source claim natural-reload follow-up/second-follow-up title 2개가 exact-field provenance wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 history-card latest-update noisy-community click-reload verification까지였으므로, 그 다음 family인 entity-card noisy single-source claim natural-reload wording round를 실제로 닫고 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:6244`, `e2e/tests/web-smoke.spec.mjs:6317`에는 `/work`가 주장한 entity-card noisy single-source claim natural-reload title wording이 실제로 반영돼 있었고, `출시일`, `2025`, `blog.example.com` 미노출과 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com provenance` 유지 truth를 직접 드러냅니다.
- entity-card noisy single-source claim natural-reload body/docs truth도 current tree와 맞았습니다. follow-up body는 `e2e/tests/web-smoke.spec.mjs:6297`, `e2e/tests/web-smoke.spec.mjs:6298`, `e2e/tests/web-smoke.spec.mjs:6300`, `e2e/tests/web-smoke.spec.mjs:6301`, `e2e/tests/web-smoke.spec.mjs:6302`, `e2e/tests/web-smoke.spec.mjs:6304`, `e2e/tests/web-smoke.spec.mjs:6305`, `e2e/tests/web-smoke.spec.mjs:6306`, `e2e/tests/web-smoke.spec.mjs:6307`, `e2e/tests/web-smoke.spec.mjs:6308`, `e2e/tests/web-smoke.spec.mjs:6310`, `e2e/tests/web-smoke.spec.mjs:6311`, `e2e/tests/web-smoke.spec.mjs:6312`에서 exclusion, positive retained fields, provenance 포함을 직접 검증하고, second-follow-up body는 `e2e/tests/web-smoke.spec.mjs:6373`, `e2e/tests/web-smoke.spec.mjs:6374`, `e2e/tests/web-smoke.spec.mjs:6376`, `e2e/tests/web-smoke.spec.mjs:6377`, `e2e/tests/web-smoke.spec.mjs:6378`, `e2e/tests/web-smoke.spec.mjs:6380`, `e2e/tests/web-smoke.spec.mjs:6381`, `e2e/tests/web-smoke.spec.mjs:6382`, `e2e/tests/web-smoke.spec.mjs:6383`, `e2e/tests/web-smoke.spec.mjs:6384`, `e2e/tests/web-smoke.spec.mjs:6386`, `e2e/tests/web-smoke.spec.mjs:6387`, `e2e/tests/web-smoke.spec.mjs:6388`에서 same truth를 직접 검증합니다. docs `README.md:184`, `README.md:185`, `docs/MILESTONES.md:97`, `docs/ACCEPTANCE_CRITERIA.md:1393`, `docs/ACCEPTANCE_CRITERIA.md:1394`, `docs/TASK_BACKLOG.md:91`, `docs/TASK_BACKLOG.md:92`도 current tree와 정렬돼 있습니다.
- focused rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim.*자연어 reload 후" --reporter=line`은 `2 passed (13.7s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- entity-card noisy single-source claim natural-reload wording family는 이번 라운드 기준으로 닫혔습니다. 다음 Claude 슬라이스는 `history-card entity-card noisy single-source claim click-reload follow-up + second-follow-up exact-field provenance wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:6393`, `e2e/tests/web-smoke.spec.mjs:6462`의 history-card click-reload title 2개는 아직 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지 truth를 직접 드러내지 않고, same body는 follow-up `e2e/tests/web-smoke.spec.mjs:6443`, `e2e/tests/web-smoke.spec.mjs:6444`, `e2e/tests/web-smoke.spec.mjs:6445`, `e2e/tests/web-smoke.spec.mjs:6447`, `e2e/tests/web-smoke.spec.mjs:6448`, `e2e/tests/web-smoke.spec.mjs:6449`, `e2e/tests/web-smoke.spec.mjs:6451`, `e2e/tests/web-smoke.spec.mjs:6452`, `e2e/tests/web-smoke.spec.mjs:6453`, `e2e/tests/web-smoke.spec.mjs:6455`, `e2e/tests/web-smoke.spec.mjs:6456`, `e2e/tests/web-smoke.spec.mjs:6457`, second-follow-up `e2e/tests/web-smoke.spec.mjs:6516`, `e2e/tests/web-smoke.spec.mjs:6517`, `e2e/tests/web-smoke.spec.mjs:6518`, `e2e/tests/web-smoke.spec.mjs:6520`, `e2e/tests/web-smoke.spec.mjs:6521`, `e2e/tests/web-smoke.spec.mjs:6522`, `e2e/tests/web-smoke.spec.mjs:6524`, `e2e/tests/web-smoke.spec.mjs:6525`, `e2e/tests/web-smoke.spec.mjs:6526`, `e2e/tests/web-smoke.spec.mjs:6528`, `e2e/tests/web-smoke.spec.mjs:6529`, `e2e/tests/web-smoke.spec.mjs:6530`에서 same exclusion, retained fields, provenance 포함을 직접 검증합니다. docs `README.md:186`, `README.md:187`, `docs/MILESTONES.md:97`, `docs/ACCEPTANCE_CRITERIA.md:1395`, `docs/ACCEPTANCE_CRITERIA.md:1396`, `docs/TASK_BACKLOG.md:93`, `docs/TASK_BACKLOG.md:94`도 이미 same truth를 고정합니다. click-reload follow-up과 second-follow-up이 같은 contract를 공유하므로, 이 둘을 한 coherent slice로 닫는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/8/2026-04-08-entity-card-noisy-single-source-claim-natural-reload-follow-up-second-follow-up-exact-field-provenance-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-latest-update-noisy-community-click-reload-follow-up-second-follow-up-exclusion-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6244,6391p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6390,6535p'`
- `nl -ba README.md | sed -n '184,188p'`
- `nl -ba docs/MILESTONES.md | sed -n '97,99p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1393,1397p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '91,95p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card noisy single-source claim.*자연어 reload 후" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- `e2e/tests/web-smoke.spec.mjs:6393`, `e2e/tests/web-smoke.spec.mjs:6462`의 history-card entity-card noisy single-source claim click-reload title 2개는 아직 retained fields와 provenance truth를 충분히 직접 드러내지 않습니다. 현재 body와 문서는 이미 `출시일`, `2025`, `blog.example.com` 미노출, `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지, `blog.example.com` provenance 포함을 직접 고정하므로, 다음 라운드에서 title wording만 맞추는 것이 가장 작은 same-family current-risk reduction입니다.
- 다른 answer-mode family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
