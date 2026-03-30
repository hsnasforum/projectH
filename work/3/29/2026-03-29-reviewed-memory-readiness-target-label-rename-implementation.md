# 2026-03-29 reviewed-memory readiness-target label rename implementation

## 변경 파일
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `plandoc/2026-03-29-reviewed-memory-readiness-target-label-contract.md`
- `plandoc/2026-03-29-reviewed-memory-satisfaction-surface-contract.md`
- `work/3/29/2026-03-29-reviewed-memory-readiness-target-label-rename-implementation.md`

## 사용 skill
- `mvp-scope`: current shipped contract와 next-step normalization question을 분리한 채 rename-only 범위를 좁게 유지하는 데 사용했습니다.
- `approval-flow-audit`: approval-backed save, historical adjunct, review acceptance, `task_log` replay가 readiness basis처럼 읽히지 않는 current safety boundary를 다시 확인했습니다.
- `doc-sync`: payload rename과 root docs / `plandoc`를 current shipped truth에 맞춰 함께 동기화했습니다.
- `release-check`: 실제 실행한 `py_compile`, `unittest`, `make e2e-test`, `git diff --check`, `rg` 결과만 기준으로 round를 닫았습니다.
- `work-log-closeout`: 저장소 규칙에 맞는 `/work` closeout 형식으로 이번 구현과 남은 리스크를 기록했습니다.

## 변경 이유
- 직전 closeout에서 current payload는 planning-only 의미를 old label `eligible_for_reviewed_memory_draft`로 담고 있어, later apply/result 쪽으로 이름상 과장될 여지가 남아 있었습니다.
- 세 target field가 coupled 되어 있으므로 one-off rename이나 partial rename이 생기면 current contract chain truth가 다시 흐려질 수 있었습니다.

## 핵심 변경
- 세 target field를 one synchronized rename-only pass로 함께 `eligible_for_reviewed_memory_draft_planning_only`로 변경했습니다:
  - `reviewed_memory_precondition_status.future_transition_target`
  - `reviewed_memory_unblock_contract.readiness_target`
  - `reviewed_memory_capability_status.readiness_target`
- 구현은 `app/web.py`의 precondition-status builder에서 source label 한 곳만 바꾸고, unblock / capability builder가 그 값을 그대로 전파하는 current structure를 유지했습니다.
- `tests/test_smoke.py`, `tests/test_web_app.py`의 aggregate expectation을 모두 narrowed label로 갱신했고, 세 field가 같은 label로 함께 나오는 coupling assertion도 추가했습니다.
- `docs/`와 `plandoc/`는 current shipped truth를 narrowed label로 맞추고, future rename wording은 제거한 뒤 later question을 `shared planning-target ref normalization`만 남기도록 정리했습니다.
- blocked / satisfied / transition / apply semantics는 그대로 유지했습니다:
  - `overall_status = blocked_all_required`
  - `unblock_status = blocked_all_required`
  - `capability_outcome = blocked_all_required`

## 검증
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- `make e2e-test`
- `git diff --check`
- `rg --pcre2 -n "eligible_for_reviewed_memory_draft(?!_planning_only)|eligible_for_reviewed_memory_draft_planning_only|future_transition_target|readiness_target|reviewed_memory_unblock_contract|reviewed_memory_capability_status|blocked_all_required|unblocked_all_required" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-readiness-target-label-contract.md`
- `rg -n "eligible_for_reviewed_memory_draft_planning_only|eligible_for_reviewed_memory_draft|future_transition_target|readiness_target|reviewed_memory_unblock_contract|reviewed_memory_capability_status|blocked_all_required|unblocked_all_required" app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-readiness-target-label-contract.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크:
  - current payload는 planning-only 의미를 old label로 담고 있어 later apply/result와 이름상 혼동될 여지가 남아 있었습니다.
- 이번 라운드에서 해소한 리스크:
  - payload와 docs가 모두 `eligible_for_reviewed_memory_draft_planning_only`를 current shipped truth로 공유하게 되었고, partial rename risk를 제거했습니다.
  - 세 target field가 같은 의미를 계속 가리킨다는 coupling rule이 코드와 회귀 테스트에서 함께 고정됐습니다.
- 여전히 남은 리스크:
  - 세 field가 같은 planning-only label을 중복 노출하고 있으므로, later normalization에서 shared planning-target ref로 줄일지 여부는 아직 open question입니다.
  - reviewed-memory store / apply / emitted transition record / repeated-signal promotion / cross-session counting / user-level memory는 계속 later layer입니다.
