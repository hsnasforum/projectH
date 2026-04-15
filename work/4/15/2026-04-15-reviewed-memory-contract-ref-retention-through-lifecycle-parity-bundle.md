# reviewed-memory contract-ref retention through lifecycle parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-contract-ref-retention-through-lifecycle-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 boundary-draft apply-separation parity bundle(`CONTROL_SEQ: 136` → verified)이 truthfully 닫힌 이후, 같은 reviewed-memory guardrail family의 다음 current-risk reduction으로 adjacent contract refs(rollback, disable, conflict, transition-audit)가 shipped emit/apply/confirm/stop/reverse/conflict visibility lifecycle 전체를 거치면서도 contract-only basis ref 상태를 유지한다는 분리를 잠그는 focused parity regression을 추가했습니다.

기존 테스트들은 초기 aggregate-shape assertion에서만 `contract_only_not_applied`, `contract_only_not_resolved`, `contract_only_not_emitted`, `aggregate_identity_and_contract_refs_retained`를 확인했고, shipped lifecycle 전체를 통과하면서 이 값들이 변하지 않는다는 focused invariant가 없었습니다.

## 핵심 변경

### `tests/test_web_app.py`

`test_recurrence_aggregate_contract_refs_retained_through_lifecycle` 메서드를 추가했습니다:

1. **rollback_stage 유지**: emit/apply/confirm/stop/reverse/conflict 각 단계마다 `contract_only_not_applied` 검증
2. **disable_stage 유지**: 각 단계에서 `contract_only_not_applied` 불변
3. **conflict_visibility_stage 유지**: 각 단계에서 `contract_only_not_resolved` 불변
4. **audit_stage 유지**: 각 단계에서 `contract_only_not_emitted` 불변
5. **post_transition_invariants 유지**: 각 단계에서 `aggregate_identity_and_contract_refs_retained` 불변
6. **aggregate_identity_ref 및 supporting refs 유지**: 모든 contract에서 initial snapshot과 동일
7. **별도 surface 분리**: 모든 contract에 `record_stage`, `transition_action`, `applied_at`, `reversed_at`, `stopped_at`가 없음을 검증

기존 boundary-draft lifecycle test와 동일한 setup 패턴(two-file → correct → aggregate emerges → emit → apply → confirm → stop → reverse → conflict visibility)을 재사용했습니다.

### 건드리지 않은 영역

- `app/serializers.py` — builder들이 이미 contract-only 값을 하드코딩하고 있어 코드 변경 불필요.
- `app/handlers/aggregate.py` — lifecycle handler들이 contract refs를 덮어쓰지 않아 변경 불필요.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` — 현재 문구가 이미 정확하여 변경 불필요.
- `e2e/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_contract_refs_retained_through_lifecycle`
  - 결과: `ok`, 2.643s
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 370 tests in 106.123s`, `OK` (기존 369 + 신규 1)
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → whitespace 경고 없음
- Playwright / `make e2e-test`는 실행하지 않았습니다. 이번 슬라이스는 serializer/handler 계약 테스트만 확인했고 browser DOM/UI는 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 테스트는 serializer builder들이 `contract_only_not_applied`, `contract_only_not_resolved`, `contract_only_not_emitted`를 하드코딩으로 반환하는 현재 구현을 잠급니다. 미래에 contract promotion을 열면 이 테스트가 의도적으로 실패하여 분리 변경을 드러냅니다.
- dirty working tree에 이미 존재하는 unrelated pending hunks(`controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등)는 건드리지 않았습니다.
- 현재 suite에는 boundary draft lifecycle parity(직전 bundle)와 contract-ref retention lifecycle parity(이번 bundle)가 별도 메서드로 존재합니다. 두 invariant 모두 동일한 lifecycle 경로를 거치지만 각각 별도의 관심사를 잠급니다.
