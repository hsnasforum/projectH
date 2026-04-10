# history-card entity-card click-reload initial + follow-up exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-click-reload-initial-follow-up-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload initial/follow-up title 2개가 exact-field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 title change와 focused rerun claim이 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 zero-strong-slot natural-reload wording family를 닫아 둔 상태였으므로, 이번 history-card entity-card click-reload wording family도 실제로 닫고 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `e2e/tests/web-smoke.spec.mjs:1112`, `e2e/tests/web-smoke.spec.mjs:1332`에는 `/work`가 주장한 history-card entity-card click-reload title wording이 실제로 반영돼 있었고, `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` truth를 직접 드러냅니다.
- same family body truth도 current tree와 맞았습니다. initial body는 `e2e/tests/web-smoke.spec.mjs:1191`, `e2e/tests/web-smoke.spec.mjs:1192`, `e2e/tests/web-smoke.spec.mjs:1195`, `e2e/tests/web-smoke.spec.mjs:1196`, `e2e/tests/web-smoke.spec.mjs:1197`, `e2e/tests/web-smoke.spec.mjs:1201`, `e2e/tests/web-smoke.spec.mjs:1202`에서 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` retention truth를 직접 검증하고, follow-up body는 `e2e/tests/web-smoke.spec.mjs:1430`, `e2e/tests/web-smoke.spec.mjs:1431`, `e2e/tests/web-smoke.spec.mjs:1433`, `e2e/tests/web-smoke.spec.mjs:1434`, `e2e/tests/web-smoke.spec.mjs:1437`, `e2e/tests/web-smoke.spec.mjs:1438`에서 same drift-prevention truth를 직접 검증합니다. docs `README.md:129`, `README.md:131`, `docs/MILESTONES.md:47`, `docs/MILESTONES.md:49`, `docs/ACCEPTANCE_CRITERIA.md:1338`, `docs/ACCEPTANCE_CRITERIA.md:1340`을 함께 대조했고, 이 중 follow-up 문구는 아직 generic wording이 남아 있습니다.
- focused rerun은 current tree에서 재현됐습니다. initial rerun `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 클릭 후 WEB badge" --reporter=line`은 `1 passed (7.7s)`였고, follow-up rerun `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반" --reporter=line`은 병렬 실행 중 한 차례 로컬 포트 충돌로 실패했지만 즉시 단독 재실행해서 `1 passed (7.8s)`였습니다. `git diff -- e2e/tests/web-smoke.spec.mjs`는 empty, `git diff --check -- e2e/tests/web-smoke.spec.mjs`는 clean, `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과는 `75`였습니다.
- `response origin badge와 answer-mode badge` generic wording은 smoke test title 기준으로 이번 라운드로 닫혔습니다. 다음 Claude 슬라이스는 `history-card entity-card click-reload follow-up docs exact-field wording clarification`으로 고정했습니다. 현재 implementation/test truth는 exact-field로 닫혔지만, docs `README.md:131`, `docs/MILESTONES.md:49`, `docs/ACCEPTANCE_CRITERIA.md:1340`, `docs/TASK_BACKLOG.md:38`은 아직 `response origin badge와 answer-mode badge drift prevention`처럼 generic wording만 남아 있습니다. same family test title/body는 이미 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` drift-prevention truth를 직접 고정하므로, 새로운 behavior를 여는 대신 same-family docs truth-sync 한 건으로 정렬하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-entity-card-click-reload-initial-follow-up-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-entity-card-zero-strong-slot-natural-reload-initial-follow-up-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1112,1447p'`
- `nl -ba README.md | sed -n '128,132p'`
- `nl -ba docs/MILESTONES.md | sed -n '46,50p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1337,1341p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '34,40p'`
- `git diff -- e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`
- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`
- `rg -n "response origin badge와 answer-mode badge|answer-mode badge가 유지됩니다|answer-mode badge가 drift하지 않습니다" e2e/tests/web-smoke.spec.mjs`
- `rg -n "response origin badge와 answer-mode badge|response origin badge, answer-mode badge|answer-mode badge가 drift하지|answer-mode badge가 유지" README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 클릭 후 WEB badge" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card 다시 불러오기 후 follow-up 질문에서 WEB badge, 설명 카드, 설명형 단일 출처, 백과 기반" --reporter=line`
- `python3 -m unittest -v`, `make e2e-test`는 이번 wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- implementation/test truth는 exact-field로 닫혔지만, docs `README.md:131`, `docs/MILESTONES.md:49`, `docs/ACCEPTANCE_CRITERIA.md:1340`, `docs/TASK_BACKLOG.md:38`은 아직 generic wording입니다. 현재 shipped contract 설명이 test/body truth보다 덜 구체적이므로, 다음 라운드에서는 same-family docs wording만 맞추는 것이 가장 작은 current-risk reduction입니다.
- 다른 answer-mode family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
