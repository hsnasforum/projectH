# latest-update noisy-community natural-reload follow-up + second-follow-up exclusion exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-latest-update-noisy-community-natural-reload-follow-up-second-follow-up-exclusion-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 latest-update noisy-community natural-reload follow-up/second-follow-up title 2개가 exclusion exact-field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 news-only natural-reload verification까지였으므로, 그 다음 family인 noisy-community natural-reload wording round를 실제로 닫고 same-family 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:5965`, `e2e/tests/web-smoke.spec.mjs:6034`에는 `/work`가 주장한 noisy-community natural-reload title wording이 실제로 반영돼 있었고, 모두 `보조 커뮤니티`, `brunch` 미노출과 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` 유지 truth를 직접 드러냅니다.
- noisy-community natural-reload body/docs truth도 current tree와 맞았습니다. follow-up body는 `e2e/tests/web-smoke.spec.mjs:6017`, `e2e/tests/web-smoke.spec.mjs:6018`, `e2e/tests/web-smoke.spec.mjs:6019`, `e2e/tests/web-smoke.spec.mjs:6021`, `e2e/tests/web-smoke.spec.mjs:6022`, `e2e/tests/web-smoke.spec.mjs:6023`, `e2e/tests/web-smoke.spec.mjs:6024`, `e2e/tests/web-smoke.spec.mjs:6026`, `e2e/tests/web-smoke.spec.mjs:6027`, `e2e/tests/web-smoke.spec.mjs:6029`에서 negative exclusion과 positive retention을 직접 검증하고, second-follow-up body는 `e2e/tests/web-smoke.spec.mjs:6089`, `e2e/tests/web-smoke.spec.mjs:6090`, `e2e/tests/web-smoke.spec.mjs:6091`, `e2e/tests/web-smoke.spec.mjs:6093`, `e2e/tests/web-smoke.spec.mjs:6094`, `e2e/tests/web-smoke.spec.mjs:6095`, `e2e/tests/web-smoke.spec.mjs:6096`, `e2e/tests/web-smoke.spec.mjs:6098`, `e2e/tests/web-smoke.spec.mjs:6099`, `e2e/tests/web-smoke.spec.mjs:6101`에서 same truth를 직접 검증합니다. docs `README.md:180`, `README.md:181`, `docs/MILESTONES.md:95`, `docs/ACCEPTANCE_CRITERIA.md:1389`, `docs/ACCEPTANCE_CRITERIA.md:1390`, `docs/TASK_BACKLOG.md:87`, `docs/TASK_BACKLOG.md:88`도 current tree와 정렬돼 있습니다.
- focused rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update noisy community source가 자연어 reload 후" --reporter=line`은 `2 passed (13.6s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- latest-update noisy-community natural-reload wording family는 이번 라운드 기준으로 닫혔습니다. 다음 Claude 슬라이스는 `history-card latest-update noisy-community click-reload follow-up + second-follow-up exclusion exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:6106`, `e2e/tests/web-smoke.spec.mjs:6173`의 history-card click-reload noisy-community title 2개만 아직 generic wording이고, same body는 `e2e/tests/web-smoke.spec.mjs:6156`, `e2e/tests/web-smoke.spec.mjs:6157`, `e2e/tests/web-smoke.spec.mjs:6158`, `e2e/tests/web-smoke.spec.mjs:6160`, `e2e/tests/web-smoke.spec.mjs:6161`, `e2e/tests/web-smoke.spec.mjs:6162`, `e2e/tests/web-smoke.spec.mjs:6163`, `e2e/tests/web-smoke.spec.mjs:6165`, `e2e/tests/web-smoke.spec.mjs:6166`, `e2e/tests/web-smoke.spec.mjs:6168`, `e2e/tests/web-smoke.spec.mjs:6227`, `e2e/tests/web-smoke.spec.mjs:6228`, `e2e/tests/web-smoke.spec.mjs:6229`, `e2e/tests/web-smoke.spec.mjs:6231`, `e2e/tests/web-smoke.spec.mjs:6232`, `e2e/tests/web-smoke.spec.mjs:6233`, `e2e/tests/web-smoke.spec.mjs:6234`, `e2e/tests/web-smoke.spec.mjs:6236`, `e2e/tests/web-smoke.spec.mjs:6237`, `e2e/tests/web-smoke.spec.mjs:6239`에서 same exclusion + positive-retention truth를 직접 검증합니다. docs `README.md:182`, `README.md:183`, `docs/MILESTONES.md:96`, `docs/ACCEPTANCE_CRITERIA.md:1391`, `docs/ACCEPTANCE_CRITERIA.md:1392`, `docs/TASK_BACKLOG.md:89`, `docs/TASK_BACKLOG.md:90`도 이미 same truth를 고정합니다. click-reload follow-up과 second-follow-up이 같은 contract를 공유하므로, 이 둘을 한 coherent slice로 닫는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,240p' work/4/8/2026-04-08-latest-update-noisy-community-natural-reload-follow-up-second-follow-up-exclusion-exact-field-wording-clarification.md`
- `sed -n '1,240p' verify/4/8/2026-04-08-latest-update-news-only-natural-reload-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5960,6105p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '6104,6245p'`
- `nl -ba README.md | sed -n '178,184p'`
- `nl -ba docs/MILESTONES.md | sed -n '94,97p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1389,1393p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '87,91p'`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "latest-update noisy community source가 자연어 reload 후" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- `e2e/tests/web-smoke.spec.mjs:6106`, `e2e/tests/web-smoke.spec.mjs:6173`의 history-card latest-update noisy-community click-reload title 2개는 아직 generic wording입니다. 현재 body와 문서는 이미 `보조 커뮤니티`, `brunch` 미노출과 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` 유지 truth를 직접 고정하므로, 다음 라운드에서 title wording만 맞추는 것이 가장 작은 same-family current-risk reduction입니다.
- entity-card noisy single-source claim family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
