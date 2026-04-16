# 2026-04-16 controller idle roam deterministic smoke verification

## 변경 파일
- `verify/4/16/2026-04-16-controller-idle-roam-deterministic-smoke-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-controller-idle-roam-deterministic-smoke.md`는 `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` 두 문서에만 남아 있던 controller smoke 설명 누락을 현재 구현 truth에 맞춘 docs-only sync라고 주장합니다.
- 이번 verification 라운드는 해당 주장이 현재 tree 기준으로도 사실인지 먼저 확인하고, markdown-only 라운드라는 범위를 넘지 않는 선에서 다음 exact slice 하나를 다시 여는 것이 목적입니다.
- `READ_FIRST`와 `SCOPE_HINT`에 따라 이번 재검증은 `git diff --check`와 직접 문구 대조를 우선하고, runtime/code rerun은 새 코드 변경이 없는 docs-only 라운드이므로 넓히지 않습니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree 기준으로 사실입니다.
  - `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`에는 모두 `window.testPickIdleTargets` + `window.getRoamBounds` 기반 deterministic idle roam bounds/desk-exclusion smoke 문구가 반영돼 있습니다.
  - 같은 내용은 이미 `controller/index.html`의 `window.getRoamBounds`, `window.testPickIdleTargets`, `e2e/tests/controller-smoke.spec.mjs`의 `idle roam targets stay within walkable bounds and outside desk exclusion rects` 시나리오, `README.md`, `docs/ACCEPTANCE_CRITERIA.md`에 선행 반영돼 있었습니다.
- 따라서 이번 `/work`는 새로운 runtime 변경이 아니라, 두 문서의 누락 표현만 현재 shipped truth에 맞춘 docs-only sync로 보는 것이 정확합니다.
- 같은 날 controller roam family에서 3회 이상 연속된 docs-only micro-loop는 확인되지 않았습니다. 다음 라운드는 같은 family의 code/test current-risk reduction으로 되돌리는 것이 맞습니다.

## 검증
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 두 문서에 deterministic idle roam bounds/desk-exclusion smoke 설명이 추가된 현재 diff 확인
- `rg -n "window.getRoamBounds|window.testPickIdleTargets|idle roam targets stay within walkable bounds and outside desk exclusion rects|deterministic idle roam bounds/desk-exclusion" controller/index.html e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: controller code, controller smoke, root docs 간 해당 문구와 test hook 정합성 확인
- `git status --short docs/MILESTONES.md docs/TASK_BACKLOG.md README.md docs/ACCEPTANCE_CRITERIA.md e2e/tests/controller-smoke.spec.mjs controller/index.html`
  - 결과: 관련 controller/docs 파일이 dirty 상태인 것은 확인했지만, 최신 `/work`가 주장한 두 문서의 sync 문구는 현재 tree에서도 위 코드/문서 표면과 일치
- `make controller-test`
  - 미재실행: 이번 `/work`는 markdown-only sync이며 변경 파일에 `controller/index.html` / `e2e/tests/controller-smoke.spec.mjs` 같은 runtime/test 파일이 없어서, 이번 verification은 `SCOPE_HINT`에 따라 direct comparison과 diff hygiene까지만 수행

## 남은 리스크
- 현재 idle roam family의 deterministic smoke는 bounds/desk-exclusion만 보호합니다. docs가 이미 설명하는 inter-agent proximity avoidance와 `_roamHistory` 기반 variety는 아직 dedicated smoke로 보호되지 않습니다.
- controller/docs 관련 dirty worktree가 계속 남아 있으므로 다음 Claude 라운드는 현재 tree 위에 접합해야 하며, unrelated hunks를 되돌리면 안 됩니다.
