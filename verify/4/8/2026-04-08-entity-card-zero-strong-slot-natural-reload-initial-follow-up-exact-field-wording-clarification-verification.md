# entity-card zero-strong-slot natural-reload initial + follow-up exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-entity-card-zero-strong-slot-natural-reload-initial-follow-up-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 zero-strong-slot natural-reload family의 initial/follow-up title 2개가 exact-field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 zero-strong-slot click-reload wording family를 닫아 둔 상태였으므로, 이번 zero-strong-slot natural-reload sibling family도 실제로 닫고 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:4014`, `e2e/tests/web-smoke.spec.mjs:4122`에는 `/work`가 주장한 zero-strong-slot natural-reload title wording이 실제로 반영돼 있었고, `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` continuity truth를 직접 드러냅니다.
- natural-reload body/docs truth도 current tree와 맞았습니다. initial body는 `e2e/tests/web-smoke.spec.mjs:4097`, `e2e/tests/web-smoke.spec.mjs:4098`, `e2e/tests/web-smoke.spec.mjs:4100`, `e2e/tests/web-smoke.spec.mjs:4101`, `e2e/tests/web-smoke.spec.mjs:4102`, `e2e/tests/web-smoke.spec.mjs:4104`, `e2e/tests/web-smoke.spec.mjs:4105`, `e2e/tests/web-smoke.spec.mjs:4106`, `e2e/tests/web-smoke.spec.mjs:4109`, `e2e/tests/web-smoke.spec.mjs:4110`, `e2e/tests/web-smoke.spec.mjs:4111`에서 same continuity truth를 직접 검증하고, follow-up body는 `e2e/tests/web-smoke.spec.mjs:4219`, `e2e/tests/web-smoke.spec.mjs:4220`, `e2e/tests/web-smoke.spec.mjs:4222`, `e2e/tests/web-smoke.spec.mjs:4223`, `e2e/tests/web-smoke.spec.mjs:4224`, `e2e/tests/web-smoke.spec.mjs:4226`, `e2e/tests/web-smoke.spec.mjs:4227`, `e2e/tests/web-smoke.spec.mjs:4228`, `e2e/tests/web-smoke.spec.mjs:4231`, `e2e/tests/web-smoke.spec.mjs:4232`, `e2e/tests/web-smoke.spec.mjs:4233`에서 same continuity truth를 직접 검증합니다. docs `README.md:150`, `README.md:151`, `docs/MILESTONES.md:68`, `docs/MILESTONES.md:69`, `docs/ACCEPTANCE_CRITERIA.md:1359`, `docs/ACCEPTANCE_CRITERIA.md:1360`, `docs/TASK_BACKLOG.md:57`, `docs/TASK_BACKLOG.md:58`도 current tree와 정렬돼 있습니다.
- focused rerun은 current tree에서 재현됐습니다. `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "zero-strong-slot.*자연어 reload" --reporter=line`은 `2 passed (13.4s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- zero-strong-slot family(click-reload + natural-reload)는 이번 라운드 기준으로 닫혔습니다. 다음 Claude 슬라이스는 `history-card entity-card click-reload initial + follow-up exact-field wording clarification`으로 고정했습니다. `e2e/tests/web-smoke.spec.mjs:1112`, `e2e/tests/web-smoke.spec.mjs:1332`의 history-card entity-card click-reload title 2개만 아직 generic wording이고, same family body는 initial `e2e/tests/web-smoke.spec.mjs:1191`, `e2e/tests/web-smoke.spec.mjs:1192`, `e2e/tests/web-smoke.spec.mjs:1195`, `e2e/tests/web-smoke.spec.mjs:1196`, `e2e/tests/web-smoke.spec.mjs:1197`, `e2e/tests/web-smoke.spec.mjs:1201`, `e2e/tests/web-smoke.spec.mjs:1202`, follow-up `e2e/tests/web-smoke.spec.mjs:1430`, `e2e/tests/web-smoke.spec.mjs:1431`, `e2e/tests/web-smoke.spec.mjs:1433`, `e2e/tests/web-smoke.spec.mjs:1434`, `e2e/tests/web-smoke.spec.mjs:1437`, `e2e/tests/web-smoke.spec.mjs:1438`에서 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` retention/drift-prevention truth를 직접 검증합니다. docs `README.md:129`, `README.md:131`, `docs/MILESTONES.md:47`, `docs/MILESTONES.md:49`, `docs/ACCEPTANCE_CRITERIA.md:1338`, `docs/ACCEPTANCE_CRITERIA.md:1340`도 same contract를 유지합니다. `rg -n "response origin badge와 answer-mode badge"` 검색 기준으로 현재 smoke file의 remaining generic title은 이 2건뿐이므로, 둘을 한 coherent slice로 닫는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-entity-card-zero-strong-slot-natural-reload-initial-follow-up-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-zero-strong-slot-click-reload-initial-follow-up-second-follow-up-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4014,4242p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1112,1575p'`
- `nl -ba README.md | sed -n '128,132p'`
- `nl -ba docs/MILESTONES.md | sed -n '46,50p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1337,1341p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `rg -n "response origin badge와 answer-mode badge|response origin badge와 answer-mode badge가|answer-mode badge가 유지됩니다|answer-mode badge가 drift하지 않습니다" e2e/tests/web-smoke.spec.mjs`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "zero-strong-slot.*자연어 reload" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- `e2e/tests/web-smoke.spec.mjs:1112`, `e2e/tests/web-smoke.spec.mjs:1332`의 history-card entity-card click-reload title 2개는 아직 exact-field truth를 충분히 직접 드러내지 않습니다. 현재 body와 문서는 이미 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` retention/drift-prevention contract를 직접 고정하므로, 다음 라운드에서는 title wording만 맞추는 것이 가장 작은 current-risk reduction입니다.
- 다른 answer-mode family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
