# 2026-03-30 aggregate-level reviewed-memory apply boundary only

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
- 최신 `/work`인 `2026-03-30-aggregate-level-transition-record-emission-only.md`와 최신 `/verify`인 `2026-03-30-aggregate-level-transition-record-emission-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 `reviewed_memory_transition_record`가 `emitted_record_only_not_applied` stage로 발행되었으나, reviewed-memory apply boundary는 열리지 않았습니다.
- 이번 슬라이스의 목표는 emitted record 위에서 apply boundary만 여는 것이었습니다.

## 핵심 변경
- `app/web.py`에 `apply_aggregate_transition(payload)` 메서드 추가:
  - `session_id`, `aggregate_fingerprint`, `canonical_transition_id`를 받아 검증
  - 해당 transition record가 `emitted_record_only_not_applied` stage인지 확인
  - `record_stage`를 `applied_pending_result`로 전환, `applied_at` 타임스탬프 추가
  - 세션에 저장 후 `reviewed_memory_transition_applied` task_log 이벤트 기록
- API route `/api/aggregate-transition-apply` 추가
- `app/templates/index.html` aggregate card 렌더링을 3-way 분기로 변경:
  - `applied_pending_result`: "적용 완료" 라벨 표시
  - `emitted_record_only_not_applied`: "검토 메모 적용 실행" 버튼 → 클릭 시 POST `/api/aggregate-transition-apply`
  - emitted record 없음 + `unblocked`: 기존 emit 폼 (사유 textarea + "검토 메모 적용 시작" 버튼)
  - `blocked`: 기존 disabled 버튼
- `e2e/tests/web-smoke.spec.mjs`: emission 후 apply 버튼 표시 → 클릭 → `applied_pending_result` + `applied_at` 검증, "적용 완료" 라벨 표시 확인
- `tests/test_smoke.py`, `tests/test_web_app.py`: 변경 없음 (기존 테스트는 emission/apply 없이 record absent를 확인하므로 여전히 유효)

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (3.9m)
- `git diff --check` — 통과

## 남은 리스크
- `record_stage = applied_pending_result`는 apply boundary가 도달했음을 뜻하지만, 실제 apply result(메모리 효과 반영)는 아직 구현되지 않았습니다.
- `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- dirty worktree가 여전히 넓습니다.
