# 2026-05-21 role routes alias cleanup

## 변경 파일
- `pipeline_runtime/role_routes.py`
- `tests/test_pipeline_runtime_schema.py`
- `work/5/21/2026-05-21-role-routes-alias-cleanup.md`

## 사용 skill
- `security-gate`: runtime route/notify normalization 변경이 operator, verify followup, advisory routing 경계를 완화하지 않는지 확인하기 위해 사용했습니다.
- `work-log-closeout`: CONTROL_SEQ 2111의 변경 파일, 검증, 남은 리스크를 `/work`에 기록하기 위해 사용했습니다.

## 변경 이유
- `role_routes.py`가 canonical 문자열 상수와 alias frozenset 상수를 라우트마다 분리해 관리하고 있었습니다.
- legacy alias가 늘어날 때 `_CANONICAL_NOTIFY_KIND_BY_LEGACY`에 누락이 생길 수 있어, 파일 내 `LEGACY_` 상수 전체를 테스트로 잠글 필요가 있었습니다.
- 기존 import 사용자는 문자열 상수와 alias frozenset 이름을 계속 참조하므로 하위 호환 이름은 유지해야 했습니다.

## 핵심 변경
- `RouteSpec(NamedTuple)`을 추가하고 각 route/notify 종류를 `RouteSpec(canonical, aliases)` 인스턴스로 정의했습니다.
- 기존 `VERIFY_FOLLOWUP_ROUTE`, `VERIFY_FOLLOWUP_ROUTE_ALIASES` 등 모듈 레벨 상수는 `RouteSpec`에서 파생되도록 유지했습니다.
- `VERIFY_TRIAGE_ONLY_REASON_ALIASES`를 추가해 triage-only legacy reason도 동일한 구조로 표현했습니다.
- `_CANONICAL_NOTIFY_KIND_BY_LEGACY`가 `LEGACY_CODEX_FOLLOWUP_ROUTE`, `LEGACY_CODEX_TRIAGE_ESCALATION`, `LEGACY_CODEX_TRIAGE_ONLY_REASON`까지 포함하도록 보완했습니다.
- `tests/test_pipeline_runtime_schema.py`에 RouteSpec 하위 호환과 legacy mapping 완전성 테스트를 추가했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/role_routes.py`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_schema -v 2>&1 | tail -5`
  - 결과: `Ran 273 tests`, `OK`
- 통과: `python3 -m unittest tests.test_turn_arbitration -v`
  - 결과: `Ran 11 tests`, `OK`
- 통과: `python3 -c "... VERIFY_FOLLOWUP_ROUTE ... VERIFY_FOLLOWUP_ROUTE_ALIASES ..."`
  - 결과: `하위 호환 OK`
- 통과: `git diff --check -- pipeline_runtime/role_routes.py tests/test_pipeline_runtime_schema.py`

## 남은 리스크
- `supervisor.py`와 `turn_arbitration.py`는 READ_FIRST로 사용 패턴만 확인했고 수정하지 않았습니다.
- 이번 변경은 route/notify normalization helper 정리이며, turn arbitration 상수 중복 정리는 범위 밖으로 남겼습니다.
- 현재 worktree에는 이전 Claude print-pipe 관련 dirty 변경과 verify/report/work 기록이 남아 있습니다. 이번 라운드에서는 되돌리거나 포함하지 않았습니다.
- 전체 repo unittest discover, browser/E2E, live runtime soak는 실행하지 않았습니다.
- commit, push, PR, merge, publish는 실행하지 않았습니다.
