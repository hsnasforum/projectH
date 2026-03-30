# 2026-03-30 aggregate-level transition-record emission verification

## 변경 파일
- `docs/NEXT_STEPS.md`
- `docs/PRODUCT_SPEC.md`
- `verify/3/30/2026-03-30-aggregate-level-transition-record-emission-verification.md`

## 사용 skill
- `round-handoff`
- `doc-sync`

## 변경 이유
- 최신 `/work`인 `2026-03-30-aggregate-level-transition-record-emission-only.md`는 aggregate-level `reviewed_memory_transition_record` emission이 구현되었다고 주장합니다.
- 최신 `/verify`인 `2026-03-30-enabled-aggregate-card-submit-boundary-verification.md`는 submit boundary까지만 검증했기 때문에 현재 기준으로 stale 여부를 다시 판정해야 했습니다.
- 현재 코드와 e2e는 실제 emitted transition record를 가리키고 있었지만, 루트 문서 일부에는 이전 `reviewed_memory_transition_record` absence / next emission-only wording과 internal `boundary_source_ref` enabled 해석이 남아 있었습니다.

## 핵심 변경
- 필수 재검증을 다시 실행했고, 현재 환경에서 `py_compile`, focused unittest, `make e2e-test`, `git diff --check`가 모두 통과함을 확인했습니다.
- 현재 코드와 e2e를 다시 대조해 아래 shipped truth를 확인했습니다:
  - aggregate card `검토 메모 적용 시작`은 `capability_outcome = unblocked_all_required`일 때만 note 입력 후 enabled 됩니다.
  - blocked 상태이거나 note가 비어 있으면 버튼은 계속 disabled입니다.
  - enabled submit은 실제 `/api/aggregate-transition` POST로 이어지고, 서버가 `reviewed_memory_transition_record`를 발행해 세션의 `reviewed_memory_emitted_transition_records`에 저장합니다.
  - emitted record는 `transition_record_version = first_reviewed_memory_transition_record_v1`, `transition_action = future_reviewed_memory_apply`, explicit `operator_reason_or_note`, `record_stage = emitted_record_only_not_applied`, `task_log_mirror_relation = mirror_allowed_not_canonical`, `emitted_at`를 가집니다.
  - `reviewed_memory_apply`와 apply result는 여전히 열리지 않았습니다.
- 최신 `/verify`는 stale로 판정했습니다. 현재 truth는 `enabled submit boundary + notice only + no emitted transition record`가 아니라 `server-emitted transition record + emitted_record_only_not_applied + no reviewed-memory apply`입니다.
- 루트 문서의 stale wording을 현재 shipped truth에 맞게 최소 범위로 sync했습니다:
  - `docs/NEXT_STEPS.md`
  - `docs/PRODUCT_SPEC.md`
- 이번 라운드에서는 코드나 테스트를 바꾸지 않았고, reviewed-memory apply나 broader state machine은 열지 않았습니다.
- 다음 최소 슬라이스는 `one truthful aggregate-level reviewed-memory apply boundary only`로 좁히는 것이 맞습니다.

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` — 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` — `Ran 176 tests in 2.278s`, `OK`
- `make e2e-test` — `12 passed (3.8m)`
- `git diff --check` — 통과
- `rg -n "reviewed_memory_transition_record|transition_record_version|canonical_transition_id|operator_reason_or_note|emitted_at|emitted_record_only_not_applied|aggregate-transition|boundary-reached notice|next truthful implementation step|검토 메모 적용 시작" app/web.py app/templates/index.html tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md` — code/e2e/docs truth 재대조에 사용

## 남은 리스크
- dirty worktree가 여전히 넓어서 다음 슬라이스도 unrelated 변경과 분리해서 좁게 진행해야 합니다.
- 현재 operator-facing aggregate card는 enabled submit까지 열렸지만, lower internal `boundary_source_ref`는 계속 `trigger_state = visible_disabled`로 직렬화됩니다. 이 차이는 현재 shipped truth의 일부이며, apply boundary를 열 때도 의도적으로 유지할지 다시 확인해야 합니다.
- focused unittest는 helper 계약을 넓게 검증하지만 `emit_aggregate_transition` HTTP 경로 자체를 직접 고정하는 단위 테스트는 여전히 약하고, 현재 emitted 경로의 end-to-end 보장은 Playwright smoke가 맡고 있습니다.
- `reviewed_memory_transition_record`는 emitted 상태일 뿐이며 `record_stage = emitted_record_only_not_applied`입니다. reviewed-memory apply와 apply result는 아직 닫혀 있습니다.
