# reviewed-memory local-effect-chain lifecycle parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-local-effect-chain-lifecycle-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 verify(`CONTROL_SEQ: 139` verify)가 source-family lifecycle parity bundle을 truthfully 닫은 후, 같은 reviewed-memory guardrail family의 다음 adjacent current-risk reduction으로 hidden local-effect chain이 shipped lifecycle 전체를 거치면서도 동일하게 유지되는지를 잠그는 focused parity regression을 추가했습니다.

기존 lifecycle tests는 boundary draft, contract refs, exact supporting refs, 그리고 source-family refs(boundary_source_ref, rollback/disable/conflict/audit source refs, applied_effect_target, reversible_effect_handle)를 emit/apply/confirm/stop/reverse/conflict visibility 전 단계에서 잠그지만, 그 아래의 internal local-effect chain(proof_record, proof_boundary, fact_source_instance, fact_source, event, event_producer, event_source, record)이 동일 lifecycle 경로에서 변하지 않는다는 focused invariant는 없었습니다.

## 핵심 변경

### `tests/test_web_app.py`

`test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle` 메서드를 추가했습니다:

1. **내부 enriched aggregate 재구축**: source-family test와 동일한 approach로 각 lifecycle 단계에서 messages → preliminary aggregate → proof store entries → enriched aggregate → source_context 재구축
2. **8개 local-effect chain builders 전체 검증**: emit/apply/confirm/stop/reverse/conflict 각 단계마다:
   - `reviewed_memory_local_effect_presence_proof_record`
   - `reviewed_memory_local_effect_presence_proof_boundary`
   - `reviewed_memory_local_effect_presence_fact_source_instance`
   - `reviewed_memory_local_effect_presence_fact_source`
   - `reviewed_memory_local_effect_presence_event`
   - `reviewed_memory_local_effect_presence_event_producer`
   - `reviewed_memory_local_effect_presence_event_source`
   - `reviewed_memory_local_effect_presence_record`
   가 initial snapshot과 동일
3. **chain 내부 공유 identity 일관성 검증**: 초기 상태에서 8개 chain member 모두의 `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`, `boundary_source_ref`, `applied_effect_id`, `present_locally_at`가 일관적인지 cross-check
4. **기존 setup 재사용**: two-file recurrence aggregate setup과 emit/apply/confirm/stop/reverse/conflict flow를 기존 lifecycle tests와 동일하게 사용

### 건드리지 않은 영역

- `app/serializers.py` — builder chain이 이미 올바르게 동작하고 있어 코드 변경 불필요.
- `app/handlers/aggregate.py` — lifecycle handler들이 local-effect chain 입력을 mutate하지 않아 변경 불필요.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` — 현재 문구가 이미 정확하여 변경 불필요.
- `e2e/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_local_effect_chain_retained_through_lifecycle`
  - 결과: `ok`, 2.668s
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 372 tests in 112.681s`, `OK` (기존 371 + 신규 1)
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → whitespace 경고 없음
- Playwright / `make e2e-test`는 실행하지 않았습니다. 이번 슬라이스는 internal builder chain의 lifecycle 안정성을 검증하는 단위 테스트만 추가했고 browser DOM/UI는 건드리지 않았기 때문입니다.

## 남은 리스크

- 이 테스트는 proof store entries와 messages가 lifecycle 동안 변하지 않는 현재 동작에 의존합니다. 미래에 lifecycle handler가 이 값들을 수정하면 의도적으로 실패합니다.
- 8개 chain member가 all-or-nothing으로 resolve되는 현재 구현을 잠급니다. 미래에 chain을 부분적으로만 build하는 변경이 있으면 이 테스트가 감지합니다.
- dirty working tree의 unrelated pending hunks는 건드리지 않았습니다.
