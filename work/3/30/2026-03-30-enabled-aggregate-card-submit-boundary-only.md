# 2026-03-30 enabled aggregate-card submit boundary only

## 변경 파일
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
- 최신 `/work`인 `2026-03-30-reviewed-memory-unblocked-all-required-path-only.md`와 최신 `/verify`인 `2026-03-30-reviewed-memory-unblocked-all-required-verification.md`를 읽고 이어받았습니다.
- 이전 라운드에서 `capability_outcome = unblocked_all_required`가 열렸으나, aggregate card `검토 메모 적용 시작` 버튼은 여전히 hardcoded `disabled = true`였습니다.
- 이번 슬라이스의 목표는 unblocked 상태에서 실제 inline submit boundary만 여는 것이었습니다.

## 핵심 변경
- `app/templates/index.html`에서 aggregate card 렌더링을 `isAggregateTriggerUnblocked(item)` 분기로 변경했습니다:
  - **unblocked일 때**: mandatory 사유 textarea(`aggregate-trigger-note`) 표시, 사유 입력 시 `검토 메모 적용 시작` 버튼 enabled, 클릭 시 boundary-reached notice 표시
  - **blocked일 때**: 기존과 동일하게 disabled 버튼 + blocked helper 텍스트
- `aggregateTriggerBlockedHelper(item)` 함수가 unblocked일 때는 `"검토 메모 적용을 시작할 수 있습니다. 사유를 입력한 뒤 시작 버튼을 누르세요."` 텍스트를 반환합니다.
- 상태 텍스트가 unblocked 묶음이 있으면 `"검토 메모 적용을 시작할 수 있는 묶음이 있습니다."` 로 변경됩니다.
- 버튼 클릭 시 서버 호출 없이 client-side notice만 표시합니다: `"검토 메모 적용 시작 경계에 도달했습니다. 실제 transition record 발행은 아직 구현되지 않았습니다."`
- `e2e/tests/web-smoke.spec.mjs`: aggregate trigger 시나리오를 업데이트하여 note 입력 → 버튼 enabled → 클릭 → notice 표시 흐름을 검증합니다.
- `reviewed_memory_transition_record`는 여전히 absent입니다.
- emitted record, apply result는 생성하지 않습니다.
- `app/web.py`, `tests/test_smoke.py`, `tests/test_web_app.py`는 변경하지 않았습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — 176 tests OK
- `make e2e-test` — 12 passed (3.8m)
- `git diff --check` — 통과

## 남은 리스크
- submit boundary는 열렸지만 실제 `reviewed_memory_transition_record` 발행은 아직 구현되지 않았습니다.
- 버튼 클릭 시 서버 호출 없이 client-side notice만 표시합니다.
- 다음 슬라이스는 실제 emitted transition record 생성입니다.
- dirty worktree가 여전히 넓습니다.
