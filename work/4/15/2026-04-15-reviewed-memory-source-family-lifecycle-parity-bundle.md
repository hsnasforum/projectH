# reviewed-memory source-family lifecycle parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-source-family-lifecycle-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 verify(`CONTROL_SEQ: 138` verify)가 exact supporting-ref lifecycle parity bundle을 truthfully 닫은 후, 같은 reviewed-memory guardrail family의 다음 adjacent current-risk reduction으로 internal source-family backers가 shipped lifecycle 전체를 거치면서도 동일하게 유지되는지를 잠그는 focused parity regression을 추가했습니다.

기존 lifecycle tests는 boundary draft, contract refs, 그리고 exact supporting refs를 emit/apply/confirm/stop/reverse/conflict visibility 전 단계에서 잠그지만, internal source-family 계층(`boundary_source_ref`, `rollback_source_ref`, `disable_source_ref`, `conflict_source_ref`, `transition_audit_source_ref`, `reviewed_memory_applied_effect_target`, `reviewed_memory_reversible_effect_handle`)이 동일 lifecycle 경로에서 변하지 않는다는 focused invariant는 없었습니다.

## 핵심 변경

### `tests/test_web_app.py`

`test_recurrence_aggregate_source_family_refs_retained_through_lifecycle` 메서드를 추가했습니다:

1. **내부 enriched aggregate 재구축**: 각 lifecycle 단계에서 public API가 반환한 messages를 사용하여 `_build_recurrence_aggregate_candidates` → `_build_reviewed_memory_local_effect_presence_proof_record_store_entries` → enriched aggregate 재구축
2. **source_context 안정성**: 각 단계에서 `_build_recurrence_aggregate_reviewed_memory_source_context`가 동일하게 resolve되는지 검증
3. **7개 source-family refs 전체 검증**: emit/apply/confirm/stop/reverse/conflict 각 단계마다:
   - `boundary_source_ref` (trigger_state: visible_disabled)
   - `applied_effect_target` (target_stage: effect_present_local_only)
   - `reversible_effect_handle` (effect_stage: handle_defined_not_applied)
   - `rollback_source_ref`
   - `disable_source_ref`
   - `conflict_source_ref`
   - `transition_audit_source_ref`
   가 initial snapshot과 동일
4. **기존 setup 재사용**: two-file recurrence aggregate setup과 emit/apply/confirm/stop/reverse/conflict flow를 기존 lifecycle tests와 동일하게 사용

### 건드리지 않은 영역

- `app/serializers.py` — resolver/builder chain이 이미 올바르게 동작하고 있어 코드 변경 불필요.
- `app/handlers/aggregate.py` — lifecycle handler들이 source-family refs 입력을 mutate하지 않아 변경 불필요.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` — 현재 문구가 이미 정확하여 변경 불필요.
- `e2e/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — ��번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_source_family_refs_retained_through_lifecycle`
  - 결과: `ok`, 2.627s
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 371 tests in 108.340s`, `OK` (기존 370 + 신규 1)
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → whitespace 경고 없음
- Playwright / `make e2e-test`는 실행하지 않았습니다. 이번 슬라이스는 internal resolver/builder chain의 lifecycle 안정성을 검증하는 단위 테스트만 추가했고 browser DOM/UI는 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 테스트�� proof store entries가 lifecycle 동안 변하지 않는다는 현재 동작에 의존합니다(lifecycle handlers는 `reviewed_memory_emitted_transition_records`만 수정하고 proof store는 건드리지 않음). 미래에 lifecycle handler가 proof store를 수정하면 이 테스트가 의도적으로 실패합니다.
- messages는 lifecycle 동안 변하지 않으므로 `_build_recurrence_aggregate_candidates(messages)`의 preliminary 결과도 동일합니다. 이는 구현의 실제 동작을 반영하지만, 미래에 handler가 messages를 수정하면 source-family refs도 바뀔 수 있어 이 테스트가 감지합니다.
- dirty working tree의 unrelated pending hunks(`controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등)는 건드리지 않았습니다.
