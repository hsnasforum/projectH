STATUS: verified
CONTROL_SEQ: 252
BASED_ON_WORK: work/4/26/2026-04-26-operator-control-resolver.md
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 252

---

# 2026-04-26 Operator Control Resolver 검증

## 이번 라운드 범위

세 개의 연속 implement 라운드를 한 번에 검증함:

1. **M42 pre-1 watcher_core re-export normalization** (`work/4/26/2026-04-26-m42-watcher-core-reexport-normalization.md`)
   - `watcher_core.py` dispatch/state/FSM re-export 제거; `__all__` 추가
   - `tests/test_watcher_core.py` import 경로 정규화 (watcher_state / verify_fsm / watcher_stabilizer)

2. **Auth operator boundary safety** (`work/4/26/2026-04-26-auth-operator-boundary.md`)
   - `auth_login_required`를 `_GATED_REASON_CODES` → `_IMMEDIATE_REASON_CODES`로 이동해 gate_24h와 결합해도 `needs_operator` 유지

3. **Shared operator control resolver** (`work/4/26/2026-04-26-operator-control-resolver.md`)
   - `pipeline_runtime.operator_autonomy.resolve_operator_control(...)` 추가
   - `pipeline_runtime/supervisor.py`, `watcher_core.py` 공유 resolver 사용으로 전환

## 검증 요약 (직접 실행)

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile pipeline_runtime/operator_autonomy.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py` | **PASS** (출력 없음) |
| `git diff --check -- [변경 파일 전체]` | **PASS** (trailing whitespace 없음) |
| `python3 -m unittest -v tests.test_operator_request_schema` | **31 tests OK** |
| `python3 -m unittest -v tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_automation_health` | **171 tests OK** |
| `python3 -m unittest -v tests.test_watcher_core` | **204 tests OK** |

기존 verify 248 대비 테스트 카운트 증가 확인:
- `test_operator_request_schema`: 29 → 31 (+2, auth_login_required stays operator_visible + resolver 회귀)
- `test_pipeline_runtime_supervisor + automation_health`: 170 → 171 (+1, auth stays operator visible)
- `test_watcher_core`: 204 → 204 (패치 경로 정규화, 카운트 유지)

## 확인한 내용

- `resolve_operator_control()`: `classify_operator_candidate`, `evaluate_stale_operator_control`, `operator_gate_marker_from_decision` 삼중 조합이 단일 shared 호출로 집중됨
- `supervisor.py` + `watcher_core.py` 양쪽이 같은 resolver를 참조해 false-stop demotion 경계 이중 조립 제거됨
- `auth_login_required` → `_IMMEDIATE_REASON_CODES`로 안전 분류: `gate_24h` 결합 시에도 `operator_eligible=True` / gate_marker 없음 고정 (테스트로 잠금)
- real-risk stop 경계 (`truth_sync_required`, safety, destructive, auth/approval-record repair) 기존 operator-visible 유지 확인

## 범위 외 (이번 검증에서 건드리지 않음)

- live supervisor/watcher soak, controller browser smoke: sandbox 제약으로 미실행
- `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`: 수정 상태 유지 (선행 라운드 산출물, 별도 커밋 예정)
- `report/gemini/**`: Gemini advisory 출력, 코드 변경 없음
- E2E/Playwright: 이번 변경이 브라우저 계약과 무관하므로 미실행

## 현재 Dirty Tree 상태

| 파일 | 라운드 | 커밋 여부 |
|------|--------|-----------|
| `watcher_core.py` | re-export norm + resolver | 미커밋 |
| `tests/test_watcher_core.py` | re-export norm | 미커밋 |
| `pipeline_runtime/operator_autonomy.py` | auth boundary + resolver | 미커밋 |
| `pipeline_runtime/supervisor.py` | resolver | 미커밋 |
| `tests/test_operator_request_schema.py` | auth boundary + resolver | 미커밋 |
| `tests/test_pipeline_runtime_supervisor.py` | auth boundary + resolver | 미커밋 |
| `README.md` | auth boundary + resolver docs | 미커밋 |
| `.pipeline/README.md` | auth boundary + resolver docs | 미커밋 |
| `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md` | M36 (선행) | 미커밋 |

Work notes (untracked): `2026-04-26-m42-watcher-core-reexport-normalization.md`, `2026-04-26-auth-operator-boundary.md`, `2026-04-26-operator-control-resolver.md`

**operator_request 248**은 B1 릴리스 게이트 특정 버킷만 승인했음. 새 3개 라운드는 그 범위 밖이므로 커밋/푸시에 별도 advisory/operator 승인 필요.

## 남은 리스크

- 새 3개 라운드 미커밋: branch audit trail 갱신 및 Draft PR #35 연장 여부 advisory 결정 필요
- M42 A1-β 다음 슬라이스: advisory 250이 방향을 제시했으나 MILESTONES.md가 "다음 advisory에서 확정" 상태이고, 계획에 없던 auth boundary + resolver 라운드가 추가되어 재확인 필요
