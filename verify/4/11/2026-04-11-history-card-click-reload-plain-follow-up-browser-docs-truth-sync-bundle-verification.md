# history-card click-reload plain-follow-up browser docs truth-sync bundle verification

## 변경 파일

- `verify/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-docs-truth-sync-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 browser smoke family 의 docs-only truth-sync bundle 이라고 주장했으므로, 실제 루트 docs 5개가 직전 browser proof 와 일치하는지만 좁게 다시 확인했습니다. 이번 라운드는 `## 변경 파일` 기준으로 markdown docs-only 였으므로 unit, Playwright, runtime 검증으로 넓히지 않고 direct file comparison 과 `git diff --check` 만 사용했습니다.

## 핵심 변경

- 최신 `/work` 의 핵심 주장 대부분은 사실입니다. 새 browser pair 자체는 루트 docs 에 반영되어 있습니다: `README.md` 124/125, `docs/TASK_BACKLOG.md` 127/128, `docs/ACCEPTANCE_CRITERIA.md` inventory bullet 2건, `docs/MILESTONES.md` shipped browser smoke bullet 2건, `docs/NEXT_STEPS.md` inventory 문장 내 pair 1회 삽입.
- smoke inventory count 도 현재 docs 기준 `125 core browser scenarios` 로 맞춰져 있습니다. `docs/ACCEPTANCE_CRITERIA.md:1352` 와 `docs/NEXT_STEPS.md:23` 이 모두 `125` 를 가리킵니다.
- 다만 최신 `/work` 는 fully truthful 하지는 않습니다. `docs/NEXT_STEPS.md:23` 는 여전히 `aligned with docs/ACCEPTANCE_CRITERIA.md:1351` 라고 적고 있는데, 실제 `docs/ACCEPTANCE_CRITERIA.md:1351` 는 Playwright webServer launch 설명이고 inventory count 헤더는 `docs/ACCEPTANCE_CRITERIA.md:1352` 입니다.
- 따라서 이번 docs bundle 은 scenario wording/count drift 대부분을 닫았지만, same-family smoke inventory cross-reference drift 1건을 남겼습니다. `/work` 본문에서 "`1351` 참조 라인을 그대로 둬도 된다" 는 취지의 설명은 사실과 다릅니다.

## 검증

- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md work/4/11`
- `nl -ba docs/NEXT_STEPS.md | sed -n '20,26p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1350,1354p'`
- `nl -ba README.md | sed -n '247,254p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '137,144p'`
- docs-only truth-sync round 이므로 unit, Playwright, `make e2e-test` 재실행은 하지 않았습니다.

## 남은 리스크

- 같은 날 같은 browser/docs family 에서 docs-only truth-sync 가 반복되었으므로, 다음 라운드는 한 줄 수정 micro-slice 가 아니라 smoke inventory cross-reference/count anchor 를 한 번에 정리하는 bounded docs cleanup bundle 이어야 합니다.
- 현재 repo dirty worktree 는 계속 남아 있습니다. 이번 verify 라운드는 최신 `/work` 의 docs family 와 next control slot 만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, `tests/`, 기존 다른 `/work` / `/verify` 변경은 건드리지 않았습니다.
