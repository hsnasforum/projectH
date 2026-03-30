# 2026-03-30 reviewed-memory correction-pattern effect activation only

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
- 최신 `/work`인 `2026-03-30-aggregate-level-reviewed-memory-apply-result-only.md`와 최신 `/verify`인 `2026-03-30-aggregate-level-reviewed-memory-apply-result-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 apply result가 `result_recorded_effect_pending`으로 기록되었으나, 실제 메모리 효과가 future responses에 반영되지 않았습니다.
- 이번 슬라이스의 목표는 same-session future responses에 reviewed-memory correction-pattern effect가 실제로 작동하는 층만 여는 것이었습니다.

## 핵심 변경
- `app/web.py` `confirm_aggregate_transition_result`에서:
  - `apply_result.result_stage`를 `result_recorded_effect_pending` 대신 `effect_active`로 설정
  - session에 `reviewed_memory_active_effects` 리스트로 active effect 저장 (effect_kind, aggregate_fingerprint, operator_reason_or_note, activated_at)
- `app/web.py` `_apply_reviewed_memory_effects` 헬퍼 메서드 추가:
  - `_handle_chat_impl`의 응답 생성 직후 호출
  - session에 active correction-pattern effects가 있으면 응답 텍스트 앞에 `[검토 메모 활성] {사유} (패턴 {fingerprint})` prefix 주입
  - streaming 중이면 `text_replace` 이벤트로 UI 즉시 갱신
- `app/templates/index.html`:
  - `applied_with_result` helper 텍스트: "검토 메모 적용 효과가 활성화되었습니다. 이후 응답에 교정 패턴이 반영됩니다."
- `e2e/tests/web-smoke.spec.mjs`:
  - result confirmation 후 `effect_active` 검증
  - "효과가 활성화되었습니다" helper 텍스트 검증
  - 새 file summary 요청 후 `[검토 메모 활성]` prefix와 operator reason이 response-box에 포함되는지 검증

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (4.2m)
- `git diff --check` — 통과

## 남은 리스크
- 현재 효과는 응답 텍스트 앞에 `[검토 메모 활성]` prefix를 주입하는 post-processing 형태입니다. 실제 모델 프롬프트 수준의 correction-pattern injection은 아직 구현되지 않았습니다.
- `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility`는 열지 않았습니다.
- repeated-signal promotion, broader durable promotion, cross-session counting은 열지 않았습니다.
- dirty worktree가 여전히 넓습니다.
