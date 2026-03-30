# 2026-03-30 aggregate-level transition record emission only

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
- 최신 `/work`인 `2026-03-30-enabled-aggregate-card-submit-boundary-only.md`와 최신 `/verify`인 `2026-03-30-enabled-aggregate-card-submit-boundary-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 aggregate card의 inline submit boundary는 열렸으나, 버튼 클릭 시 서버 호출 없이 client-side notice만 표시하고 `reviewed_memory_transition_record`는 여전히 absent이었습니다.
- 이번 슬라이스의 목표는 실제 transition record emission만 구현하는 것이었습니다.

## 핵심 변경
- `app/web.py`에 `emit_aggregate_transition(payload)` 메서드 추가:
  - `session_id`, `aggregate_fingerprint`, `operator_reason_or_note`를 받아 검증
  - 해당 aggregate가 `unblocked_all_required` 상태인지 확인
  - `reviewed_memory_transition_record` 객체 생성:
    - `transition_record_version = first_reviewed_memory_transition_record_v1`
    - `canonical_transition_id = transition-local-{uuid}`
    - `transition_action = future_reviewed_memory_apply`
    - `aggregate_identity_ref` + supporting refs
    - `operator_reason_or_note` (사용자 입력)
    - `record_stage = emitted_record_only_not_applied`
    - `task_log_mirror_relation = mirror_allowed_not_canonical`
    - `emitted_at` (UTC 타임스탬프)
  - session에 `reviewed_memory_emitted_transition_records` 리스트로 저장
  - task_log에 `reviewed_memory_transition_emitted` 이벤트 기록
- `_build_recurrence_aggregate_reviewed_memory_transition_record` 메서드가 이제 stored record를 lookup:
  - `capability_outcome = unblocked_all_required`일 때만 진행
  - aggregate의 내부 `_reviewed_memory_emitted_transition_records`에서 fingerprint 일치하는 record 검색
  - 유효한 `canonical_transition_id`, `operator_reason_or_note`, `emitted_at`, `transition_action = future_reviewed_memory_apply`가 있을 때만 반환
- `_build_recurrence_aggregate_candidates`에 `emitted_transition_records` 파라미터 추가, `_serialize_session`에서 전달
- serialization 시 internal key `_reviewed_memory_emitted_transition_records` 필터링
- API route `/api/aggregate-transition` 추가
- `app/templates/index.html`: 버튼 클릭 시 `/api/aggregate-transition`에 POST → transition record 발행 후 notice 표시 + session 갱신
- `e2e/tests/web-smoke.spec.mjs`: transition record가 실제로 payload에 존재하는지 검증 (version, action, note, stage, id, emitted_at)
- `tests/test_smoke.py`, `tests/test_web_app.py`: 변경 없음 (기존 테스트는 emission 없이 record absent를 확인하므로 여전히 유효)

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (4.0m)
- `git diff --check` — 통과

## 남은 리스크
- `reviewed_memory_transition_record`는 이제 emitted 상태이지만 `record_stage = emitted_record_only_not_applied`입니다.
- reviewed-memory apply는 구현되지 않았습니다.
- `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- dirty worktree가 여전히 넓습니다.
