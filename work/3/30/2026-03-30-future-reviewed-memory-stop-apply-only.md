# 2026-03-30 reviewed-memory stop-apply / reversal / conflict visibility truth reconciliation

## 변경 파일
- 없음 (이번 라운드는 `/work` closeout truth 복구만 수행)

## 사용 skill
- 없음

## 변경 이유
- 최신 `/work` closeout이 `future_reviewed_memory_stop_apply`까지만 기술되어 있었으나, 현재 코드·문서·테스트는 이미 reversal과 conflict visibility까지 구현 완료된 상태입니다.
- 같은 날 `/verify` rerun 결과에서도 이 gap을 확인하고 `/work` truth reconciliation을 다음 라운드 목표로 지정했습니다.
- 이번 라운드는 코드·문서·테스트를 변경하지 않고, `/work` canonical closeout을 현재 truth에 맞게 한 번만 복구합니다.

## 핵심 변경
이번 라운드에서 app/docs/test 변경은 없습니다. 아래는 현재 코드가 실제로 ship하고 있는 truth입니다.

### stop-apply (`future_reviewed_memory_stop_apply`) — 이미 구현됨
- `app/web.py`의 `stop_apply_aggregate_transition(payload)` 메서드
- API route `/api/aggregate-transition-stop`
- 동작: `applied_with_result` → `stopped`, `result_stage` → `effect_stopped`, `reviewed_memory_active_effects`에서 해당 항목 제거
- UI: aggregate card에 `applied_with_result` 상태에서 "적용 중단" 버튼 표시, 클릭 후 "적용 중단됨" 라벨 + helper 텍스트
- 효과: stop 후 새 요청에서 `[검토 메모 활성]` prefix 사라짐

### reversal (`future_reviewed_memory_reversal`) — 이미 구현됨
- `app/web.py`의 `reverse_aggregate_transition(payload)` 메서드
- API route `/api/aggregate-transition-reverse`
- 동작: `stopped` → `reversed`, `result_stage` → `effect_reversed`, `reversed_at` 추가
- UI: aggregate card에 `stopped` 상태에서 "적용 되돌리기" 버튼 표시
- aggregate identity, supporting refs, contracts 유지

### conflict visibility (`future_reviewed_memory_conflict_visibility`) — 이미 구현됨
- `app/web.py`의 `check_aggregate_conflict_visibility(payload)` 메서드
- API route `/api/aggregate-transition-conflict-check`
- 동작: `reversed` 상태에서 별도의 conflict-visibility transition record 생성
  - `transition_action = future_reviewed_memory_conflict_visibility`
  - `record_stage = conflict_visibility_checked`
  - 평가된 `conflict_entries`, `conflict_entry_count`
  - `source_apply_transition_ref`로 원본 apply record 참조
- UI: aggregate card에 `reversed` 상태에서 "충돌 확인" 버튼 표시
- conflict visibility record는 apply transition record와 분리, 원본을 변경하지 않음

### 테스트 현황
- `tests/test_web_app.py`에 stop/reverse/conflict handler dispatch regression 포함
- `e2e/tests/web-smoke.spec.mjs`에 aggregate 시나리오 per-test timeout `120_000` 조정 포함

## 검증
이번 라운드에서 코드·테스트 변경이 없으므로 검증을 새로 실행하지 않았습니다.
같은 날짜 `/verify` rerun 결과를 인용합니다 (`verify/3/30/` 기준):
- `python3 -m py_compile app/web.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_web_app` — `Ran 97 tests in 1.857s`, `OK`
- `cd e2e && npx playwright test -g "same-session recurrence aggregate"` — `1 passed (1.0m)`
- `make e2e-test` — `12 passed (4.4m)`
- `git diff --check` — 통과

## 남은 리스크
- aggregate Playwright scenario는 약 60초 소요. timeout 상향(120s)으로 green이지만, latency 원인은 아직 분리되지 않았습니다.
- dirty worktree가 넓습니다: `tests/test_web_app.py`, `e2e/tests/web-smoke.spec.mjs`, 삭제된 `/work`·`/verify` 파일, untracked `backup/`·`report/`가 함께 있습니다.
- repeated-signal promotion, broader durable promotion, cross-session counting은 아직 열리지 않았습니다.
