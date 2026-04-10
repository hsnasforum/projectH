# history-card entity-card click-reload follow-up docs exact-field wording clarification verification

날짜: 2026-04-08

## 변경 파일
- `verify/4/8/2026-04-08-history-card-entity-card-click-reload-follow-up-docs-exact-field-wording-clarification-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 history-card entity-card click-reload follow-up docs 4곳이 exact-field wording으로 정렬됐다고 보고했습니다. 이번 라운드에서는 그 docs-only change가 current tree 기준으로 truthful한지 다시 확인할 필요가 있었습니다.
- same-day latest `/verify`는 history-card entity-card click-reload test title wording family를 닫아 둔 상태였으므로, 이번 docs truth-sync sibling family도 실제로 닫고 다음 exact slice를 하나로 고정해야 했습니다.

## 핵심 변경
- latest `/work`의 observable end state는 truthful하셨습니다. `README.md:131`, `docs/MILESTONES.md:49`, `docs/ACCEPTANCE_CRITERIA.md:1340`, `docs/TASK_BACKLOG.md:38`에는 `/work`가 주장한 follow-up docs wording이 실제로 반영돼 있었고, `history-card entity-card` prefix와 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` drift-prevention truth를 직접 드러냅니다.
- docs truth는 current test/body와도 맞았습니다. same family test title은 `e2e/tests/web-smoke.spec.mjs:1332`에서 exact-field wording으로 이미 정렬돼 있었고, body는 `e2e/tests/web-smoke.spec.mjs:1430`, `e2e/tests/web-smoke.spec.mjs:1431`, `e2e/tests/web-smoke.spec.mjs:1433`, `e2e/tests/web-smoke.spec.mjs:1434`, `e2e/tests/web-smoke.spec.mjs:1437`, `e2e/tests/web-smoke.spec.mjs:1438`에서 same drift-prevention truth를 직접 검증합니다. initial side reference도 `e2e/tests/web-smoke.spec.mjs:1112`, `e2e/tests/web-smoke.spec.mjs:1191`, `e2e/tests/web-smoke.spec.mjs:1195`, `e2e/tests/web-smoke.spec.mjs:1201`에 남아 있어 entity-card initial/follow-up family의 contract를 current tree 기준으로 복원할 수 있습니다.
- docs-only verification 범위에서는 claimed check도 truthful했습니다. `git diff -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`는 empty였고, `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`는 clean이었습니다. 이번 `/work`는 docs-only wording clarification이므로 Playwright 재실행을 새로 주장하지 않았고, 저도 browser rerun은 추가로 돌리지 않았습니다.
- `response origin badge와 answer-mode badge` generic wording은 same family docs follow-up 기준으로 이번 라운드로 닫혔습니다. 다음 Claude 슬라이스는 `history-card entity-card click-reload initial docs entity-prefix wording clarification`으로 고정했습니다. 현재 follow-up docs는 exact-field로 정렬됐지만, initial docs `README.md:129`, `docs/MILESTONES.md:47`, `docs/ACCEPTANCE_CRITERIA.md:1338`, `docs/TASK_BACKLOG.md:36`은 아직 `history-card`만 적고 있어 바로 아래 latest-update sibling line들과 나란히 놓였을 때 entity-card 대상임이 덜 직접적입니다. same family initial test/body는 이미 `e2e/tests/web-smoke.spec.mjs:1112`, `e2e/tests/web-smoke.spec.mjs:1191`, `e2e/tests/web-smoke.spec.mjs:1195`, `e2e/tests/web-smoke.spec.mjs:1201`에서 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` truth를 직접 고정하므로, 새로운 behavior를 여는 대신 initial docs prefix만 entity-card truth에 맞춰 정렬하는 편이 가장 작고 truthful합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,220p' work/4/8/2026-04-08-history-card-entity-card-click-reload-follow-up-docs-exact-field-wording-clarification.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-history-card-entity-card-click-reload-initial-follow-up-exact-field-wording-clarification-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba README.md | sed -n '129,131p'`
- `nl -ba docs/MILESTONES.md | sed -n '47,49p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1338,1340p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '36,38p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1112,1447p'`
- `git diff -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `python3 -m unittest -v`, `make e2e-test`, Playwright rerun은 이번 docs-only wording verification 범위를 넘어가므로 재실행하지 않았습니다.

## 남은 리스크
- follow-up docs truth는 정렬됐지만, initial docs `README.md:129`, `docs/MILESTONES.md:47`, `docs/ACCEPTANCE_CRITERIA.md:1338`, `docs/TASK_BACKLOG.md:36`은 아직 `history-card`만 적고 있어 entity-card 대상임이 덜 직접적입니다. 현재 test/body truth는 이미 entity-card initial contract를 직접 고정하므로, 다음 라운드에서는 initial docs prefix만 맞추는 것이 가장 작은 same-family current-risk reduction입니다.
- 다른 answer-mode family는 이번 verification 범위 밖이라 재판정하지 않았습니다.
