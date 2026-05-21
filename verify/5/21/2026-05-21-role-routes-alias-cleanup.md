# verify: 2026-05-21 role_routes alias cleanup (C1/C2)

## 대상 work
`work/5/21/2026-05-21-role-routes-alias-cleanup.md`

## 검증 결과: READY

## 재실행 검증

| 검사 | 결과 |
|---|---|
| `py_compile` role_routes.py | PASS |
| `unittest` 273+11개 | PASS |
| 하위 호환 + LEGACY 매핑 완전성 | OK (7개 전부) |
| `git diff --check` | PASS |

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| RouteSpec(NamedTuple) | role_routes.py:6 | ✓ |
| 7개 RouteSpec 인스턴스 | role_routes.py:20–47 | ✓ |
| VERIFY_FOLLOWUP_ROUTE = VERIFY_FOLLOWUP.canonical | role_routes.py:49 | ✓ |
| _CANONICAL_NOTIFY_KIND_BY_LEGACY LEGACY 7개 매핑 완전 | role_routes.py | ✓ |
| 매핑 누락 시 테스트 실패하도록 잠금 | test_pipeline_runtime_schema.py | ✓ |
