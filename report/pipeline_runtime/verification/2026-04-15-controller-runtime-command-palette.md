# 2026-04-15 controller runtime command palette verification

## 검증 범위
- `controller/index.html`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 실행한 검증
- `node - <<'JS' ... new Function(script) ... JS`
- `python3 -m unittest -v tests.test_controller_server`

## 결과
- controller inline script parse 확인 통과
- controller server 관련 테스트 12건 통과
- HTML 정적 계약에서 아래를 계속 확인했습니다.
  - `/api/runtime/status`
  - `/api/runtime/start`
  - `/api/runtime/stop`
  - `/api/runtime/restart`
  - `/api/runtime/capture-tail`
  - `submitRuntimeCommand()`
  - `runtime-command-input`
- `/api/runtime/exec` 같은 arbitrary command endpoint는 추가되지 않았습니다.

## 해석
- 이번 변경은 “웹에서 CLI처럼 입력” 요구를 충족하지만, 실제 실행은 기존 runtime API allowlist에만 매핑됩니다.
- 따라서 browser controller UI는 여전히 controller HTTP only 경계를 유지하고, runtime truth writer ownership도 바뀌지 않습니다.

## 메모
- `attach`는 기존 attach API를 호출할 뿐이며 브라우저 안에 셸을 직접 여는 기능이 아닙니다.
- `tail` 명령은 focus lane과 text toggle을 operator 쪽에서 빠르게 전환하는 UX shortcut 성격이 강합니다.
