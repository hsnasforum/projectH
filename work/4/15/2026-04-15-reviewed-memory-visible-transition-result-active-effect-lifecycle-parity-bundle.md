# reviewed-memory visible transition-result-active-effect lifecycle parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-visible-transition-result-active-effect-lifecycle-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

직전 verify(`CONTROL_SEQ: 140` verify)가 hidden local-effect-chain lifecycle parity bundle을 truthfully 닫은 후, 같은 reviewed-memory guardrail family의 다음 adjacent current-risk reduction으로 shipped visible transition/result/active-effect loop이 lifecycle 전체에서 정확하고 일관되게 동작하는지를 잠그는 focused parity regression을 추가했습니다.

기존 lifecycle tests는 hidden backers(boundary draft, contract refs, supporting refs, source-family refs, local-effect chain)의 불변성을 잠그지만, 사용자에게 직접 보이는 visible surfaces — `reviewed_memory_transition_record`의 `record_stage` 진행, `apply_result`의 `result_stage` 진행, `reviewed_memory_active_effects` 멤버십, `[검토 메모 활성]` prefix 동작 — 을 shipped lifecycle 전체에서 직접 잠그는 focused regression은 없었습니다.

## 핵심 변경

### `tests/test_web_app.py`

`test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle` 메서드를 추가했습니다:

1. **record_stage 진행 검증**: emit(`emitted_record_only_not_applied`) → apply(`applied_pending_result`) → confirm(`applied_with_result`) → stop(`stopped`) → reverse(`reversed`) 각 단계에서 정확한 stage 값
2. **apply_result.result_stage 진행 검증**: confirm(`effect_active`) → stop(`effect_stopped`) → reverse(`effect_reversed`)
3. **identity 안정성 검증**: 모든 단계에서 `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`, `canonical_transition_id`, `transition_action`, `operator_reason_or_note`가 초기 값과 동일
4. **active effects 멤버십 검증**: confirm 후 `reviewed_memory_active_effects`에 정확한 entry 추가, stop 후 제거
5. **`[검토 메모 활성]` prefix 동작 검증**: confirm 후 새 chat에서 prefix 포함 + operator reason 포함, stop 후 prefix 부재, reverse 후 prefix 부재
6. **conflict visibility 검증**: reverse 후 conflict visibility check 성공, conflict_visibility_record에 정확한 identity

### 건드리지 않은 영역

- `app/serializers.py` — 변경 불필요.
- `app/handlers/aggregate.py` — 변경 불필요.
- `app/handlers/chat.py` — `[검토 메모 활성]` prefix 로직이 이미 올바르게 동작하고 있어 변경 불필요.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` — 현재 문구가 이미 정확하여 변경 불필요.
- `e2e/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle`
  - 결과: `ok`, 2.768s
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 373 tests in 119.502s`, `OK` (기존 372 + 신규 1)
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → whitespace 경고 없음
- Playwright / `make e2e-test`는 실행하지 않았습니다. 이번 슬라이스는 handler/service 계약과 `[검토 메모 활성]` prefix를 mock provider를 통해 검증했고, browser DOM/UI selector는 건드리지 않았기 때문입니다.

## 남은 리스크

- `[검토 메모 활성]` prefix 검증은 mock provider를 사용합니다. 실제 model provider에서 response text가 다르게 생성되면 prefix 삽입 위치가 달라질 수 있지만, 이는 현재 mock 기반 unit test 범위 밖입니다.
- 이 테스트는 `RecordStage`와 `ResultStage` enum의 현재 값과 진행 순서를 잠급니다. 미래에 stage 추가/변경 시 의도적으로 실패합니다.
- dirty working tree의 unrelated pending hunks는 건드리지 않았습니다.
