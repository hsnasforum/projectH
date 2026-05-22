# 2026-05-21 turn arbitration verify-followup alias derivation

## 변경 파일
- `pipeline_runtime/turn_arbitration.py`
- `tests/test_turn_arbitration.py`
- `work/5/21/2026-05-21-turn-arbitration-verify-followup-alias-derivation.md`

## 사용 skill
- `security-gate`: runtime turn/route alias 정규화 변경이 operator, verify, advisory 경계를 완화하지 않고 local helper derivation에만 머무는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 실행하지 않은 검증, 남은 리스크를 `/work`에 남기기 위해 사용했습니다.

## 변경 이유
- 직전 `role_routes.py` 정리에서 verify-followup canonical 값과 alias set이 `RouteSpec`에서 파생되도록 정리됐습니다.
- `turn_arbitration.py`에는 여전히 `codex_followup`만 직접 매핑하는 `LEGACY_WATCHER_TURN_ALIASES`가 남아 있어, verify-followup alias family가 바뀔 때 drift가 생길 수 있었습니다.
- watcher turn 이름의 기존 출력은 유지하면서 alias source를 `role_routes`의 shared alias set으로 좁히는 것이 이번 handoff의 목적이었습니다.

## 핵심 변경
- `pipeline_runtime/turn_arbitration.py`에서 `LEGACY_CODEX_FOLLOWUP_ROUTE` 직접 import를 제거했습니다.
- `VERIFY_FOLLOWUP_ROUTE_ALIASES`를 import하고, `LEGACY_WATCHER_TURN_ALIASES`를 해당 alias set에서 파생되도록 바꿨습니다.
- `legacy_watcher_turn_name("verify_followup")`와 legacy alias인 `codex_followup`이 계속 `verify_followup`으로 수렴하는 기존 동작은 유지했습니다.
- `tests/test_turn_arbitration.py`에 `VERIFY_FOLLOWUP_ROUTE_ALIASES`의 모든 값이 `legacy_watcher_turn_name()`에서 `VERIFY_FOLLOWUP_ROUTE`로 해석되는 targeted test를 추가했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/turn_arbitration.py tests/test_turn_arbitration.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest -v tests.test_turn_arbitration`
  - 결과: `Ran 12 tests in 0.002s`, `OK`.
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_schema.RoleRoutesTest`
  - 결과: `Ran 2 tests in 0.001s`, `OK`.
- 통과: `git diff --check -- pipeline_runtime/turn_arbitration.py tests/test_turn_arbitration.py work/5/21/`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- 이번 변경은 turn alias derivation에 한정되며, `pipeline_runtime/supervisor.py`, watcher dispatch logic, control writers, operator autonomy, lane vendor commands, wrapper event logic은 수정하지 않았습니다.
- live `claude`, tmux/session access, controller/browser server, Playwright, full smoke, long soak는 실행하지 않았습니다.
- 전체 repo unittest discover는 실행하지 않았습니다. 이번 검증은 turn arbitration과 RouteSpec compatibility에 맞춘 targeted checks입니다.
- 현재 worktree에는 이전 Claude print-pipe 계열 dirty 변경과 여러 `/work`, `/verify`, `report/gemini` 기록이 남아 있습니다. 이번 라운드에서는 handoff 범위 밖 변경을 되돌리거나 포함하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
