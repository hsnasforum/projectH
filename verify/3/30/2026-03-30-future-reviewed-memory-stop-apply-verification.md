## 변경 파일
- `docs/NEXT_STEPS.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `verify/3/30/2026-03-30-future-reviewed-memory-stop-apply-verification.md`

## 사용 skill
- `round-handoff`
- `doc-sync`

## 변경 이유
- 최신 `/work`가 `future_reviewed_memory_stop_apply` 구현을 주장하고 있어, 직전 `/verify`의 effect-activation truth가 stale인지 현재 코드·문서·검증 재실행 기준으로 다시 판정할 필요가 있었습니다.
- 루트 docs 일부는 current code truth 자체는 맞았지만, next-step wording이 `reversal/conflict_visibility`처럼 두 슬라이스를 묶고 있어 다음 handoff 원칙과 어긋나 있었습니다.

## 핵심 변경
- 최신 `/verify`인 `2026-03-30-reviewed-memory-correction-pattern-effect-activation-verification.md`는 stale로 판정했습니다. 현재 코드는 effect activation 위에서 `future_reviewed_memory_stop_apply`까지 구현되어 있고, 직전 note는 그 층을 검증하지 못했습니다.
- `app/web.py` 기준 현재 `stop_apply_aggregate_transition(payload)`가 실제로 `/api/aggregate-transition-stop` POST와 연결되며, same `canonical_transition_id`를 유지한 채 `record_stage = stopped`, `stopped_at`, `apply_result.result_stage = effect_stopped`를 기록합니다.
- 같은 경로에서 session `reviewed_memory_active_effects`에서 해당 `transition_ref`를 제거하므로, 이후 응답에는 `[검토 메모 활성]` prefix가 더 이상 붙지 않습니다.
- `app/templates/index.html` 기준 `적용 중단` 버튼은 `applied_with_result` branch에서만 노출됩니다. 현재 구현에서 `applied_with_result`는 `confirm_aggregate_transition_result(...)`가 `apply_result.result_stage = effect_active`를 함께 기록할 때만 열리므로, shipped behavior 기준으로는 effect active 뒤에만 보인다고 판정했습니다.
- root docs의 next-step wording은 최소 범위로 sync했습니다. `NEXT_STEPS`, `PRODUCT_SPEC`, `ARCHITECTURE`에서 next slice를 `future_reviewed_memory_reversal` 하나로 좁히고 `future_reviewed_memory_conflict_visibility`는 later로 남겼습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 176 tests in 2.756s`
  - `OK`
- `make e2e-test`
  - `12 passed (4.3m)`
- `git diff --check`
  - 통과
- `rg -n "stop_apply_aggregate_transition|aggregate-transition-stop|적용 중단|record_stage = stopped|effect_stopped|reviewed_memory_active_effects|\\[검토 메모 활성\\]|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility|next implementation step|next slice" app/web.py app/templates/index.html tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
  - stop-apply code path, e2e contract, docs wording 재대조 완료

## 남은 리스크
- `tests/test_smoke.py`와 `tests/test_web_app.py`는 stop-apply route를 직접 고정하지 않고, 핵심 보장은 주로 Playwright e2e와 code-path 재대조에 기대고 있습니다.
- `stop_apply`는 `reversal`이 아니고, transition history 삭제나 broader memory reset도 아닙니다. 다음 라운드에서 reversal/conflict_visibility를 같이 열면 scope가 깨집니다.
- dirty worktree가 넓으므로 다음 라운드도 unrelated 변경과 엄격히 분리해서 진행해야 합니다.
