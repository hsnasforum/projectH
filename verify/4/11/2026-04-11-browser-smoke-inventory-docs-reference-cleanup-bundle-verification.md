# browser smoke inventory docs reference cleanup bundle verification

## 변경 파일

- `verify/4/11/2026-04-11-browser-smoke-inventory-docs-reference-cleanup-bundle-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work` 가 browser smoke inventory family 의 docs-only reference cleanup bundle 이라고 주장했으므로, 변경된 markdown docs 와 직전 검증에서 지적한 stale anchor 가 실제로 정리되었는지만 좁게 다시 확인했습니다. 이번 라운드는 `## 변경 파일` 기준으로 docs-only 였으므로 unit, Playwright, runtime 검증으로 넓히지 않고 direct file comparison, targeted `rg`, `git diff --check` 만 사용했습니다.

## 핵심 변경

- 최신 `/work` 는 이번에는 truthful 합니다. [docs/NEXT_STEPS.md:23](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L23) 는 더 이상 `docs/ACCEPTANCE_CRITERIA.md:1351` 같은 brittle line anchor 를 쓰지 않고, `docs/ACCEPTANCE_CRITERIA.md` 의 `## Test Gates` 아래 `### Current Gates` bullet 을 가리키는 stable section reference 로 바뀌어 있습니다.
- root docs 재스캔 결과, browser smoke inventory count 는 현재 두 곳만 `125 core browser scenarios` 를 가리킵니다: [docs/ACCEPTANCE_CRITERIA.md:1352](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1352), [docs/NEXT_STEPS.md:23](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L23). 이번 family 에서 문제였던 `123 core browser scenarios`, `docs/ACCEPTANCE_CRITERIA.md:1351`, `docs/ACCEPTANCE_CRITERIA.md:1352` hard-coded anchor 는 root docs 에 남아 있지 않습니다.
- 최신 `/work` 의 범위 주장도 현재 트리와 맞습니다. 이번 cleanup bundle 은 docs-only 로 닫혔고, 별도 code/test/runtime 변경 증거는 보이지 않습니다.

## 검증

- `rg -n "123 core browser scenarios|125 core browser scenarios|docs/ACCEPTANCE_CRITERIA\\.md:1351|docs/ACCEPTANCE_CRITERIA\\.md:1352" README.md docs/*.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '20,24p'`
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md work/4/11`
- docs-only cleanup round 이므로 unit, Playwright, `make e2e-test` 재실행은 하지 않았습니다.

## 남은 리스크

- same-family docs truth gap 자체는 현재 닫힌 것으로 보입니다. 다만 같은 날 browser smoke inventory docs drift 가 여러 번 반복되었고, 아직 이를 자동으로 잡아 주는 focused regression 이 없습니다. 다음 current-risk reduction 은 또 다른 docs prose 수정이 아니라 이 family 를 위한 작은 docs parity regression 이어야 합니다.
- 현재 repo dirty worktree 는 계속 남아 있습니다. 이번 verify 라운드는 최신 docs family 와 next control slot 만 다뤘고, `controller/`, `pipeline_gui/`, `pipeline_runtime/`, `tests/`, 기존 다른 `/work` / `/verify` 변경은 건드리지 않았습니다.
