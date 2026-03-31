# 2026-03-30 future_reviewed_memory_reversal only 

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
- 최신 `/work`인 `2026-03-30-future-reviewed-memory-stop-apply-only.md`와 최신 `/verify`인 `2026-03-30-future-reviewed-memory-stop-apply-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 `future_reviewed_memory_stop_apply`까지 열렸으나, `future_reviewed_memory_reversal`은 열리지 않았습니다. 
- 이번 슬라이스의 목표는 stop_apply 위에서 reversal 한 층만 여는 것이었습니다.

## 핵심 변경
- `app/web.py`에 `reverse_aggregate_transition(payload)` 메서드 추가:
  - `session_id`, `aggregate_fingerprint`, `canonical_transition_id`를 받아 검증
  - 해당 transition record가 `stopped` stage인지 확인 (active → stop → reverse 순서 보장)
  - `record_stage`를 `reversed`로 전환, `reversed_at` 타임스탬프 추가
  - `apply_result.result_stage`를 `effect_reversed`로 전환
  - aggregate identity, supporting refs, contracts는 유지 (audit trace 보존)
  - 세션에 저장 후 `reviewed_memory_transition_reversed` task_log 이벤트 기록
- API route `/api/aggregate-transition-reverse` 추가
- `app/templates/index.html` aggregate card 렌더링에 새 분기 추가:
  - `reversed`: "적용 되돌림 완료" 라벨 + "적용 효과가 완전히 철회되었습니다" helper 텍스트
  - `stopped`: 기존 "적용 중단됨" 라벨 + 새 "적용 되돌리기" 버튼 (danger class)
- `e2e/tests/web-smoke.spec.mjs`:
  - stop 후 "적용 되돌리기" 버튼 클릭 → `reversed` + `effect_reversed` + `reversed_at` 검증
  - "적용 되돌림 완료" 라벨과 helper 텍스트 확인
  - `canonical_transition_id` 유지 확인

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (4.2m)
- `git diff --check` — 통과

## 남은 리스크
- `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- repeated-signal promotion, broader durable promotion, cross-session counting은 열지 않았습니다.
- stop_apply와 reversal은 별개 사실로 유지: stop은 "효과 중단", reversal은 "적용 철회".
- dirty worktree가 여전히 넓습니다.
