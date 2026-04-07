# entity-card dual-probe natural-reload follow-up browser-anchor source-path-exact-field wording clarification verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-follow-up-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 entity-card dual-probe natural-reload follow-up browser anchor 두 개가 source-path plurality와 exact-field contract를 제목에서 직접 드러내도록 정리되었다고 보고했습니다. 이번 라운드에서는 그 wording change와 claimed rerun이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `.pipeline/claude_handoff.md`는 이미 끝난 follow-up slice를 아직 가리키고 있었으므로, 검증 truth를 남긴 뒤 같은 family의 다음 exact slice를 하나로 다시 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:4606`은 `source path(pearlabyss.com/200, pearlabyss.com/300)`를, `e2e/tests/web-smoke.spec.mjs:4735`는 `WEB badge`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반 · 백과 기반`을 제목에 직접 드러내고 있습니다.
- follow-up dual-probe natural-reload body/docs truth도 current tree와 맞습니다. source-path body `e2e/tests/web-smoke.spec.mjs:4723`, `e2e/tests/web-smoke.spec.mjs:4724`와 exact-field body `e2e/tests/web-smoke.spec.mjs:4785`, `e2e/tests/web-smoke.spec.mjs:4789`, `e2e/tests/web-smoke.spec.mjs:4791`, `e2e/tests/web-smoke.spec.mjs:4792`, `e2e/tests/web-smoke.spec.mjs:4793`는 `README.md:155`, `README.md:156`, `docs/MILESTONES.md:73`, `docs/MILESTONES.md:74`, `docs/ACCEPTANCE_CRITERIA.md:1364`, `docs/ACCEPTANCE_CRITERIA.md:1365`, `docs/TASK_BACKLOG.md:62`, `docs/TASK_BACKLOG.md:63`와 정렬돼 있습니다.
- rerun 결과도 `/work`와 맞았습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up" --reporter=line`은 `2 passed (13.5s)`였고, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다. 검증 시점의 `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty였으므로, 이번 라운드는 persisted tree와 rerun truth를 기준으로 확인했습니다.
- 다음 Claude 슬라이스는 `entity-card dual-probe natural-reload second-follow-up browser-anchor source-path-exact-field wording clarification`으로 고정했습니다. second-follow-up combined title `e2e/tests/web-smoke.spec.mjs:4798`은 아직 generic wording만 남기지만, same body `e2e/tests/web-smoke.spec.mjs:4852`, `e2e/tests/web-smoke.spec.mjs:4856`, `e2e/tests/web-smoke.spec.mjs:4858`, `e2e/tests/web-smoke.spec.mjs:4859`, `e2e/tests/web-smoke.spec.mjs:4860`, `e2e/tests/web-smoke.spec.mjs:4864`, `e2e/tests/web-smoke.spec.mjs:4865`와 docs `README.md:164`, `docs/MILESTONES.md:84`, `docs/ACCEPTANCE_CRITERIA.md:1375`, `docs/TASK_BACKLOG.md:73`는 exact URL pair와 response-origin truth를 이미 직접 가리킵니다.

## 검증
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-dual-probe-natural-reload-follow-up-browser-anchor-source-path-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-dual-probe-natural-reload-initial-browser-anchor-source-path-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4598,4870p'`
- `nl -ba README.md | sed -n '153,165p'`
- `nl -ba docs/MILESTONES.md | sed -n '71,85p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1362,1376p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '60,74p'`
- `rg -n "entity-card dual-probe 자연어 reload 후 follow-up|entity-card dual-probe 자연어 reload 후 두 번째 follow-up|pearlabyss.com/ko-KR/Board/Detail\\?_boardNo=(200|300)|WEB|설명 카드|설명형 다중 출처 합의|공식 기반|백과 기반" e2e/tests/web-smoke.spec.mjs README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card dual-probe 자연어 reload 후 follow-up" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 browser-anchor wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- dual-probe natural-reload second-follow-up combined browser-anchor title `e2e/tests/web-smoke.spec.mjs:4798`은 still generic wording만 남아 있습니다.
- initial/follow-up/second-follow-up 외 다른 family(crimson, click-reload, zero-strong-slot, latest-update)의 동일 패턴 wording은 이번 라운드 범위 밖입니다.
