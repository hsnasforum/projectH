# 2026-04-16 controller idle free roam polish socket-blocked verification

## 변경 파일
- `verify/4/16/2026-04-16-controller-idle-free-roam-polish-socket-blocked-verification.md`
- `.pipeline/operator_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- `STATUS: implement` seq 196 `controller-office-idle-agent-free-roam-polish` handoff가 같은 세션에서 이미 완료된 상태라, 같은 handoff를 다시 열지 않고 현재 tree에 들어온 변경을 먼저 truthfully 재검증해야 했습니다.
- 이번 triage의 목적은 idle free-roam polish가 실제로 tree에 반영돼 있는지 확인하고, handoff에 적힌 필수 검증 `make controller-test`를 다시 돌린 뒤에만 다음 control outcome 하나를 고르는 것이었습니다.
- 그러나 현재 Codex 환경에서는 local socket 생성이 다시 막혀 있어 controller smoke rerun이 불가능했습니다. 이는 next-slice ambiguity가 아니라 현재 라운드 truth-sync blocker입니다.

## 핵심 변경
- 현재 tree에는 seq 196 handoff 범위의 정적 흔적이 존재합니다.
  - `controller/index.html`에 `WALKABLE_BOUNDS`, `DESK_RECTS`, `_roamHistory`, `_glanceCooldown`, `_staleTimer`, 45% free-walk 선택, direct open-floor path, micro-drift가 들어와 있습니다.
  - `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`에도 widened roam zone, walkable bounds, desk exclusion, stacking 방지, visit-history penalty, free-walk, direct path, varied linger 설명이 반영돼 있습니다.
- 하지만 handoff가 요구한 runtime 검증은 현재 환경에서 재실행되지 않았습니다.
  - `make controller-test`는 `controller.server` webServer startup 단계에서 `PermissionError: [Errno 1] Operation not permitted`로 실패했습니다.
  - 최소 `socket.socket().bind(('127.0.0.1', 0))` probe도 같은 `PermissionError`로 실패했습니다.
- 따라서 seq 197은 새 Claude 구현 handoff가 아니라 `.pipeline/operator_request.md`의 `STATUS: needs_operator`로 닫고, operator가 verification 환경 또는 static-only 허용 여부를 결정해야 합니다.

## 검증
- `git diff --check -- controller/index.html README.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `rg -n "WALKABLE_BOUNDS|DESK_RECTS|_roamHistory|_staleTimer|_glanceCooldown|Math.random\\(\\) < 0\\.45|direct walk|micro-drift|stale-position|data-fatigue" controller/index.html README.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 결과: idle free-roam polish와 docs sync의 정적 흔적 확인
- `make controller-test`
  - 결과: 실패. Playwright `webServer` startup 중 `PermissionError: [Errno 1] Operation not permitted`
- `python3 - <<'PY' ... socket.socket().bind(('127.0.0.1', 0)) ... PY`
  - 결과: 실패. `PermissionError: [Errno 1] Operation not permitted`

## 남은 리스크
- seq 196 idle free-roam polish는 현재 static diff로만 확인됐고, required controller smoke rerun은 현 환경에서 truthfully 통과하지 못했습니다.
- 최신 persistent `/work`는 여전히 `work/4/16/2026-04-16-controller-deterministic-fatigue-transition-smoke.md`입니다. seq 196 handoff는 handoff 지시대로 `/work` note 없이 진행된 상태라, 이번 `/verify`가 현재 triage truth를 대신 기록합니다.
- `.pipeline/claude_handoff.md` seq 196은 파일로 남아 있어도 seq 197 `needs_operator`가 이를 supersede해야 합니다.
