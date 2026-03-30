# 2026-03-30 reviewed-memory unblocked-all-required path only

## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/NEXT_STEPS.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음

## 변경 이유
- 최신 `/work`인 `2026-03-30-reviewed-memory-capability-basis-materialization-only.md`와 최신 `/verify`인 `2026-03-30-reviewed-memory-capability-basis-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 `reviewed_memory_capability_basis`가 materialized되었으나, `_build_recurrence_aggregate_reviewed_memory_capability_status` 메서드가 basis present 시에도 hardcoded `blocked_all_required`를 반환하도록 의도적으로 제한되어 있었습니다.
- 이번 슬라이스의 목표는 basis present 시 `capability_outcome = unblocked_all_required` path만 여는 것이었습니다.

## 핵심 변경
- `app/web.py`의 `_build_recurrence_aggregate_reviewed_memory_capability_status(...)` 메서드에서 hardcoded `capability_outcome = "blocked_all_required"`를 제거하고, `expected_capability_basis is not None`일 때 `"unblocked_all_required"`, 아닐 때 `"blocked_all_required"`로 분기하도록 변경했습니다. (3줄 변경)
- `tests/test_smoke.py`: `aggregate_with_store`의 capability_outcome 기대값을 `unblocked_all_required`로 변경.
- `tests/test_web_app.py`: serialized session에서 나온 aggregate들의 capability_outcome 기대값을 `unblocked_all_required`로 변경. basis가 pop된 `aggregate_with_support_only` / `aggregate_with_fake_source_refs`의 status assertion은 `blocked_all_required`로 유지.
- `e2e/tests/web-smoke.spec.mjs`: aggregate trigger box의 capability 텍스트를 `unblocked_all_required`로 변경.
- aggregate card `검토 메모 적용 시작` 버튼은 여전히 hardcoded `disabled = true`로 유지됩니다 (enabled submit flow 미개방).
- `reviewed_memory_transition_record`는 여전히 absent입니다.
- emitted record, apply result는 열지 않았습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (3.6m)
- `git diff --check` — 통과

## 남은 리스크
- `reviewed_memory_capability_status.capability_outcome`이 이제 `unblocked_all_required`이지만, aggregate card 버튼은 여전히 hardcoded disabled입니다.
- `reviewed_memory_transition_record`는 여전히 absent입니다.
- enabled submit flow, emitted record, apply result는 여전히 닫혀 있습니다.
- dirty worktree가 여전히 넓습니다.
