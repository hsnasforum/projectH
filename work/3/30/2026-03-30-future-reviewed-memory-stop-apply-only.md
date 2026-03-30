# 2026-03-30 future_reviewed_memory_stop_apply only

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
- 최신 `/work`인 `2026-03-30-reviewed-memory-correction-pattern-effect-activation-only.md`와 최신 `/verify`인 `2026-03-30-reviewed-memory-correction-pattern-effect-activation-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 reviewed-memory correction-pattern effect가 활성화되었으나, `future_reviewed_memory_stop_apply`는 열리지 않았습니다.
- 이번 슬라이스의 목표는 활성화된 effect 위에서 stop_apply 한 층만 여는 것이었습니다.

## 핵심 변경
- `app/web.py`에 `stop_apply_aggregate_transition(payload)` 메서드 추가:
  - `session_id`, `aggregate_fingerprint`, `canonical_transition_id`를 받아 검증
  - 해당 transition record가 `applied_with_result` stage인지 확인
  - `record_stage`를 `stopped`로 전환, `stopped_at` 타임스탬프 추가
  - `apply_result.result_stage`를 `effect_stopped`로 전환
  - `reviewed_memory_active_effects`에서 해당 `transition_ref` 항목 제거
  - 세션에 저장 후 `reviewed_memory_transition_stopped` task_log 이벤트 기록
- API route `/api/aggregate-transition-stop` 추가
- `app/templates/index.html` aggregate card 렌더링에 새 분기 추가:
  - `stopped`: "적용 중단됨" 라벨 + "검토 메모 적용이 중단되었습니다" helper 텍스트
  - `applied_with_result`: 기존 "결과 확정 완료" 라벨 + 새 "적용 중단" 버튼 (danger class)
- `e2e/tests/web-smoke.spec.mjs`:
  - effect 활성 후 "적용 중단" 버튼 클릭 → `stopped` + `effect_stopped` 검증
  - "적용 중단됨" 라벨과 helper 텍스트 확인
  - stop 후 새 file summary 요청에서 `[검토 메모 활성]` prefix가 사라지는지 검증

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (4.3m)
- `git diff --check` — 통과

## 남은 리스크
- `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- repeated-signal promotion, broader durable promotion, cross-session counting은 열지 않았습니다.
- dirty worktree가 여전히 넓습니다.
