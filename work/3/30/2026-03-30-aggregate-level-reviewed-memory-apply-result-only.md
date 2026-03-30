# 2026-03-30 aggregate-level reviewed-memory apply result only

## 변경 파일
- `app/web.py`
- `app/templates/index.html`
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
- 최신 `/work`인 `2026-03-30-aggregate-level-reviewed-memory-apply-boundary-only.md`와 최신 `/verify`인 `2026-03-30-aggregate-level-reviewed-memory-apply-boundary-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 apply boundary(`applied_pending_result`)까지 열렸으나, 실제 apply result는 구현되지 않았습니다.
- 이번 슬라이스의 목표는 `applied_pending_result` 위에서 one truthful apply result만 여는 것이었습니다.

## 핵심 변경
- `app/web.py`에 `confirm_aggregate_transition_result(payload)` 메서드 추가:
  - `session_id`, `aggregate_fingerprint`, `canonical_transition_id`를 받아 검증
  - 해당 transition record가 `applied_pending_result` stage인지 확인
  - `record_stage`를 `applied_with_result`로 전환
  - `apply_result` 객체 첨부:
    - `result_version = first_reviewed_memory_apply_result_v1`
    - `applied_effect_kind = reviewed_memory_correction_pattern`
    - `applied_scope = same_session_exact_recurrence_aggregate_only`
    - `aggregate_identity_ref`
    - `transition_ref = canonical_transition_id`
    - `result_stage = result_recorded_effect_pending`
    - `result_at` (UTC 타임스탬프)
  - `result_at` 타임스탬프 추가
  - 세션에 저장 후 `reviewed_memory_transition_result_confirmed` task_log 이벤트 기록
- API route `/api/aggregate-transition-result` 추가
- `app/templates/index.html` aggregate card 렌더링을 4-way 분기로 변경:
  - `applied_with_result`: "결과 확정 완료" 라벨 + applied_effect_kind 표시
  - `applied_pending_result`: "검토 메모 적용 결과 확정" 버튼 → 클릭 시 POST `/api/aggregate-transition-result`
  - `emitted_record_only_not_applied`: 기존 "검토 메모 적용 실행" 버튼
  - emitted record 없음 + `unblocked`: 기존 emit 폼
  - `blocked`: 기존 disabled 버튼
- `e2e/tests/web-smoke.spec.mjs`: apply boundary 후 결과 확정 버튼 → 클릭 → `applied_with_result` + `apply_result` 구조 검증, "결과 확정 완료" 라벨 확인
- `tests/test_smoke.py`, `tests/test_web_app.py`: 변경 없음

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (3.9m)
- `git diff --check` — 통과

## 남은 리스크
- `apply_result.result_stage = result_recorded_effect_pending`는 결과가 기록되었지만 실제 메모리 효과(후속 응답에 반영)는 아직 활성화되지 않았음을 의미합니다.
- `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- repeated-signal promotion, broader durable promotion, cross-session counting은 열지 않았습니다.
- dirty worktree가 여전히 넓습니다.
