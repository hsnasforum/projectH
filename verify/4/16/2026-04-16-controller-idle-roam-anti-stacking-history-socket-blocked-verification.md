# 2026-04-16 controller idle roam anti-stacking history socket-blocked verification

## 변경 파일
- `verify/4/16/2026-04-16-controller-idle-roam-anti-stacking-history-socket-blocked-verification.md`
- `.pipeline/operator_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-controller-idle-roam-anti-stacking-history-deterministic-smoke.md`는 `controller/index.html`의 controller-local read-only test hook 2건, `e2e/tests/controller-smoke.spec.mjs`의 deterministic smoke 2건, 그리고 root docs 4건 sync를 주장합니다.
- 이번 verification 라운드는 해당 구현 주장이 현재 tree와 일치하는지 다시 확인하고, `/work`가 적은 필수 검증 `make controller-test`를 가장 좁은 범위에서 재실행하는 것이 목적입니다.
- 그러나 현재 Codex 환경에서는 controller `webServer`가 필요한 로컬 소켓 생성 자체가 다시 차단되어 있어, runtime rerun이 truthfully 완료되지 않았습니다. 이는 next-slice ambiguity가 아니라 현재 `/work` 검증에 직접 걸리는 truth-sync blocker입니다.

## 핵심 변경
- 최신 `/work`의 정적 구현 주장은 현재 tree 기준으로 대체로 일치합니다.
  - `controller/index.html`에는 `window.testAntiStacking(name, otherX, otherY, count)`와 `window.testHistoryPenalty(name, historyIndices, count)`가 존재합니다.
  - `e2e/tests/controller-smoke.spec.mjs`에는 anti-stacking proximity avoidance smoke와 `_roamHistory` penalty smoke가 추가돼 있습니다.
  - `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`에도 controller smoke가 anti-stacking과 history penalty까지 커버한다는 설명이 반영돼 있습니다.
- 다만 현재 dirty worktree에는 같은 파일들에 이번 슬라이스와 무관한 누적 hunks도 함께 존재합니다. 이번 verification은 최신 `/work`가 주장한 anti-stacking/history smoke surface가 실제로 추가돼 있는지에 한해 정적 대조했습니다.
- 최신 `/work`의 핵심 검증 주장은 현재 환경에서 재입증되지 않았습니다.
  - `make controller-test`는 Playwright `webServer` startup 중 `controller.server`가 `PermissionError: [Errno 1] Operation not permitted`로 실패했습니다.
  - 최소 `socket.socket()` probe도 같은 `PermissionError`로 실패했습니다.
- 따라서 seq 200은 새 Claude implement handoff가 아니라 `.pipeline/operator_request.md`의 `STATUS: needs_operator`로 닫는 것이 맞습니다.

## 검증
- `git diff -- controller/index.html e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: `window.testAntiStacking`, `window.testHistoryPenalty`, anti-stacking/history smoke 2건, 관련 docs wording diff 확인
- `rg -n "window.testAntiStacking|window.testHistoryPenalty|idle roam avoids proximity to other idle agents|idle roam deprioritizes recently visited spots" controller/index.html e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: controller code, controller smoke, root docs 간 해당 hook/문구 정합성 확인
- `git diff --check -- controller/index.html e2e/tests/controller-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- `make controller-test`
  - 결과: 실패. Playwright `webServer` startup 중 `controller.server` socket 생성 단계에서 `PermissionError: [Errno 1] Operation not permitted`
- `python3 - <<'PY' ... socket.socket() ... PY`
  - 결과: 실패. `socket.socket()` 생성 단계에서 같은 `PermissionError: [Errno 1] Operation not permitted`

## 남은 리스크
- 최신 `/work`는 정적 diff 기준으로는 설계/문서 surface가 맞지만, 필수 controller smoke rerun이 현재 환경에서 막혀 있어 `8 passed (6.7s)`를 현재 verification 라운드에서 재확인하지 못했습니다.
- 이 상태에서 다음 Claude implement handoff를 열면 anti-stacking/history smoke의 실제 runtime 통과 여부를 다시 입증하지 못한 채 다음 라운드로 넘어가게 됩니다.
- 환경이 풀리더라도 이번 슬라이스가 커버하지 않는 roam 휴리스틱(stale-position timer, micro-drift, glance, free-walk ratio, wander interval distribution)은 여전히 별도 deterministic smoke 밖에 남아 있습니다.
