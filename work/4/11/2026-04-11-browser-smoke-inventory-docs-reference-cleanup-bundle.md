# browser smoke inventory docs reference cleanup bundle

## 변경 파일

- `docs/NEXT_STEPS.md`
- `work/4/11/2026-04-11-browser-smoke-inventory-docs-reference-cleanup-bundle.md`

## 사용 skill

- `superpowers:using-superpowers`
- `doc-sync`

## 변경 이유

직전 docs-only 라운드(`work/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-docs-truth-sync-bundle.md`)는 browser smoke inventory count 를 `123 → 125` 로 올리고 새 click-reload composer plain-follow-up 페어를 5개 루트 docs 에 정확히 한 번씩 추가하는 부분은 true 하게 닫았습니다. 그러나 검증 라운드(`verify/4/11/2026-04-11-history-card-click-reload-plain-follow-up-browser-docs-truth-sync-bundle-verification.md`)가 같은 가족 안에 남은 docs drift 하나를 지적했습니다. `docs/NEXT_STEPS.md:23` 이 여전히 `aligned with docs/ACCEPTANCE_CRITERIA.md:1351` 를 가리키고 있지만, 실제 inventory count 헤더는 count 를 업데이트하면서 `docs/ACCEPTANCE_CRITERIA.md:1352` 로 한 줄 이동했고, `:1351` 라인은 현재 Playwright webServer launch 설명입니다.

같은 날 같은 가족 안에서 또 하나의 작은 docs 마이크로 라운드를 찍지 않도록, 이 슬라이스는 해당 한 줄 드리프트를 닫으면서 동시에 required root docs set(`README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`, `docs/TASK_BACKLOG.md`)에 다른 stale smoke inventory 앵커가 있는지 한 번에 스캔해 같이 정리했습니다.

handoff 가 권장한 "prefer stable file/section references over brittle hard-coded line references where possible" 를 따라, 이번 수정은 `docs/ACCEPTANCE_CRITERIA.md:1351` 이라는 깨지기 쉬운 하드코딩 라인 앵커를 고정된 section anchor(`### Current Gates` bullet under `## Test Gates` in `docs/ACCEPTANCE_CRITERIA.md`)로 교체합니다. 이렇게 하면 같은 section 의 bullet 이 앞뒤로 한 줄씩 움직여도 이 reference 가 다시 stale 해지지 않습니다.

## 핵심 변경

### `docs/NEXT_STEPS.md`

23 라인의 inventory 설명 중 `aligned with \`docs/ACCEPTANCE_CRITERIA.md:1351\`` 부분만 `aligned with the \`### Current Gates\` bullet under \`## Test Gates\` in \`docs/ACCEPTANCE_CRITERIA.md\`` 로 교체했습니다. 나머지 긴 inventory 문장은 건드리지 않았습니다.

- 교체 전: `Playwright smoke currently covers 125 core browser scenarios (document-level browser coverage inventory count, aligned with \`docs/ACCEPTANCE_CRITERIA.md:1351\`, not the raw \`test(...)\` count in \`e2e/tests/web-smoke.spec.mjs\`), …`
- 교체 후: `Playwright smoke currently covers 125 core browser scenarios (document-level browser coverage inventory count, aligned with the \`### Current Gates\` bullet under \`## Test Gates\` in \`docs/ACCEPTANCE_CRITERIA.md\`, not the raw \`test(...)\` count in \`e2e/tests/web-smoke.spec.mjs\`), …`

이 교체는 count 자체(`125 core browser scenarios`)와 new click-reload composer plain-follow-up 페어 wording, 뒤이어 나오는 전체 inventory, 그리고 다른 bullet 들을 건드리지 않았습니다.

### 스캔 결과 — 다른 root docs 에는 추가 drift 없음

handoff 가 지정한 `rg -n "123 core browser scenarios|125 core browser scenarios|docs/ACCEPTANCE_CRITERIA\\.md:1351|docs/ACCEPTANCE_CRITERIA\\.md:1352" README.md docs/*.md` 를 돌려 root docs set 을 한 번에 스캔한 결과는 아래와 같고, 다른 stale 앵커가 없음을 확인했습니다.

- `README.md` → 매치 0건. README 는 번호 목록 기반이고 ACCEPTANCE_CRITERIA 로 하드코딩 라인 앵커가 없습니다. 별도 작업 필요 없음.
- `docs/ACCEPTANCE_CRITERIA.md:1352` → `Playwright smoke covers 125 core browser scenarios (document-level browser coverage inventory count, not the raw test(...) count in e2e/tests/web-smoke.spec.mjs):` 로 count 는 이미 `125`. 자체 참조이므로 수정 불필요.
- `docs/MILESTONES.md` → 매치 0건. 직전 라운드에서 새 페어를 browser smoke bullet 묶음에 추가했고, `123 / 125 core browser scenarios` 같은 count anchor 를 사용하지 않습니다. 별도 작업 필요 없음.
- `docs/NEXT_STEPS.md` → 23 라인 하나 — 이번 라운드의 유일한 수정 대상. count `125` 는 유지하면서 line anchor 만 section anchor 로 교체했습니다.
- `docs/TASK_BACKLOG.md` → 매치 0건. 직전 라운드에서 127/128 번 항목을 추가했고, 자체 번호 체계를 쓰지 약간 ACCEPTANCE_CRITERIA 라인 앵커를 사용하지 않습니다. 별도 작업 필요 없음.

`.pipeline/claude_handoff.md`, `work/**`, `verify/**` 에서의 매치는 handoff 자기 참조와 과거 closeout / verification 기록이므로 이번 슬라이스의 정리 대상이 아닙니다. 역사적 기록 파일(`work/`, `verify/`)은 건드리지 않았습니다.

### 건드리지 않은 영역

- `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md` 등 본문 — 변경 없음.
- `e2e/tests/web-smoke.spec.mjs`, `app/static/app.js`, `app/handlers/*`, `core/*`, `tests/*`, `controller/*`, `pipeline_gui/*`, `watcher_core.py`, `pipeline_runtime/*`, `scripts/*`, `.pipeline/*`, agent/skill 설정, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md` 등 — 이번 슬라이스 범위 밖.

## 검증

- `rg -n "123 core browser scenarios|125 core browser scenarios|docs/ACCEPTANCE_CRITERIA\\.md:1351|docs/ACCEPTANCE_CRITERIA\\.md:1352" README.md docs/*.md` (Grep tool)
  - 결과: `docs/ACCEPTANCE_CRITERIA.md:1352` 에서 `125 core browser scenarios` 1건(자체 inventory 헤더), `docs/NEXT_STEPS.md:23` 에서 `125 core browser scenarios` 1건(교체된 inventory 설명). 다른 root docs 에 `123 core browser scenarios` 또는 `docs/ACCEPTANCE_CRITERIA.md:1351` / `docs/ACCEPTANCE_CRITERIA.md:1352` 하드코딩 앵커는 남아 있지 않습니다.
- `git diff --check -- README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/TASK_BACKLOG.md work/4/11` → whitespace 경고 없음.
- handoff 지시대로 docs-only 슬라이스라 Playwright, `make e2e-test`, 전체 `tests.test_smoke` / `tests.test_web_app`, type check 재실행은 하지 않았습니다.

## 남은 리스크

- 이번 수정은 `docs/NEXT_STEPS.md:23` 한 줄의 앵커 스타일만 바꿉니다. `125` count 나 new click-reload composer plain-follow-up 페어 wording 은 그대로 유지했습니다. 미래에 browser smoke 가 또 바뀌어 count 가 변경되면 여전히 `README.md` 번호 목록, `docs/ACCEPTANCE_CRITERIA.md:1352`(inventory 헤더), `docs/NEXT_STEPS.md:23` 세 곳을 같이 올려야 일치가 유지됩니다. `docs/TASK_BACKLOG.md` 의 shipped 번호 목록도 shipped 되는 경우에는 같이 올려 주세요.
- section anchor(`### Current Gates` bullet under `## Test Gates` in `docs/ACCEPTANCE_CRITERIA.md`)는 section 이름이 바뀌면 다시 stale 해질 수 있습니다. 하지만 section 이름 변경은 bullet line 이 한 줄 움직이는 것보다 훨씬 드물고, 변경 시 인간 reviewer 가 쉽게 알아채므로 line anchor 보다 견고합니다.
- 현재 repo 는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/`, 기존 `docs/*` 일부, 기존 `/work`, `/verify` dirty 상태입니다. 이 슬라이스는 해당 pending 파일들을 되돌리거나 커밋하지 않았고, 오직 `docs/NEXT_STEPS.md` 한 줄과 이 closeout 노트만 추가했습니다. handoff 의 dirty worktree 경고와 "browser smoke inventory docs family 밖은 건드리지 말라" 제약을 유지했습니다.
