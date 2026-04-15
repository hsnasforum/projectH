# reviewed-memory precondition-status blocked-only parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-precondition-status-blocked-only-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

Gemini arbitration(`CONTROL_SEQ: 134`)이 docs-sync helper family 를 truthfully 닫은 뒤 reviewed-memory guardrail family 로 복귀를 권고했습니다. `docs/NEXT_STEPS.md:106` 의 현재 우선순위도 동일합니다.

이 슬라이스는 shipped reviewed-memory loop 에서 blocked-only precondition surface 와 capability/apply surface 의 분리를 explicit regression 으로 잠그는 데 집중했습니다. 기존 테스트들은 larger integration flow 안에서 이 값들을 incidentally 확인했지만, 분리 자체를 직접 이름 붙여 잠그는 focused invariant 테스트가 없었습니다.

## 핵심 변경

### `tests/test_web_app.py`

`WebAppServiceTest` 에 신규 테스트 method 1개 추가:

**`test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked`**

다음 분리 invariant 를 직접 잠급니다:

1. **Precondition/unblock 은 항상 blocked**: `reviewed_memory_precondition_status.overall_status == "blocked_all_required"`, `reviewed_memory_unblock_contract.unblock_status == "blocked_all_required"` — capability 가 unblocked 되더라도 변하지 않음.
2. **Ordered 5 preconditions 고정**: `reviewed_memory_boundary_defined`, `rollback_ready_reviewed_memory_effect`, `disable_ready_reviewed_memory_effect`, `conflict_visible_reviewed_memory_scope`, `operator_auditable_reviewed_memory_transition` — 순서와 항목이 정확히 일치.
3. **Capability outcome 분리**: shipped capability basis 가 있으면 `capability_outcome == "unblocked_all_required"`, basis 를 제거하면 `"blocked_all_required"` 로 돌아감 — precondition/unblock 은 양쪽 모두 `"blocked_all_required"` 유지.
4. **Support-only signals 차단**: review acceptance, approval-backed save, historical adjuncts, task-log replay 를 모두 넣어도 `_build_recurrence_aggregate_reviewed_memory_capability_basis` → `None`, `capability_outcome` → `"blocked_all_required"`, precondition/unblock 도 여전히 `"blocked_all_required"`.

### 건드리지 않은 영역

- `app/serializers.py` — 검사 결과 precondition_status 와 unblock_contract builder 는 이미 값을 하드코딩으로 반환하고 있어 코드 변경 불필요.
- `app/handlers/aggregate.py` — emit_aggregate_transition 의 gating 이 이미 `capability_outcome` 을 올바르게 사용하고 있어 변경 불필요.
- `docs/NEXT_STEPS.md` — 현재 문구가 이미 분리를 정확히 기술하고 있어 변경 불필요.
- `tests/test_smoke.py` — `test_web_app.py` 에서 separation invariant 를 충분히 잠갔기 때문에 duplicate 추가 불필요.
- `e2e/tests/web-smoke.spec.mjs`, `app/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 368 tests in 116.203s`, `OK`.
  - 신규 `test_recurrence_aggregate_precondition_blocked_stays_fixed_when_capability_unblocked` 도 `ok`.
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_smoke.py tests/test_web_app.py docs/NEXT_STEPS.md` → whitespace 경고 없음.
- Playwright / `make e2e-test` 는 실행하지 않았습니다. 이번 슬라이스는 serializer/handler 계약 테스트만 추가했고 browser DOM/UI 는 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 테스트는 `overall_status` 와 `unblock_status` 가 하드코딩된 `"blocked_all_required"` 를 반환하는 현재 구현을 잠급니다. 미래에 precondition satisfaction 을 열면 이 테스트가 의도적으로 실패하여 분리가 변경되었음을 드러냅니다.
- 저장소는 여전히 `controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등에 dirty 상태가 있습니다. 이 슬라이스는 pending 파일을 되돌리거나 커밋하지 않았고, `tests/test_web_app.py` 에 focused invariant 테스트 추가와 이 closeout 노트만 작성했습니다.
