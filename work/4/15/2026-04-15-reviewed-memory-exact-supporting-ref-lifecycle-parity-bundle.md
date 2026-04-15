# reviewed-memory exact supporting-ref lifecycle parity bundle

## 변경 파일

- `tests/test_web_app.py`
- `work/4/15/2026-04-15-reviewed-memory-exact-supporting-ref-lifecycle-parity-bundle.md`

## 사용 skill

- 없음

## 변경 이유

최신 `/verify`(`CONTROL_SEQ: 137` verify)가 직전 contract-ref retention lifecycle bundle을 확인한 결과, stage retention / no-leak / rerun command 면에서는 truthful이지만 supporting refs coverage 설명이 실제 테스트보다 넓다는 점을 지적했습니다. 구체적으로:

- `test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle`는 `supporting_source_message_refs`와 `supporting_candidate_refs`는 잠그지만 optional `supporting_review_refs`는 lifecycle 전 단계에서 검증하지 않았습니다.
- `test_recurrence_aggregate_contract_refs_retained_through_lifecycle`는 rollback contract에서만 `supporting_source_message_refs`와 `supporting_candidate_refs`를 직접 비교하고, disable / conflict / transition-audit contract에서는 `aggregate_identity_ref`와 stage 값만 비교했습니다. optional `supporting_review_refs`는 어느 contract에서도 lifecycle 전 단계 비교되지 않았습니다.

이번 슬라이스는 이 exact supporting-ref parity gap만 닫습니다.

## 핵심 변경

### `tests/test_web_app.py`

**boundary draft lifecycle test 보강:**
- `assert_boundary_draft_unchanged` helper에 optional `supporting_review_refs` 비교 추가 — initial snapshot에 `supporting_review_refs`가 있으면 lifecycle 각 단계마다 동일한지 검증

**contract refs lifecycle test 보강:**
- `assert_contract_refs_unchanged` helper를 loop 기반으로 리팩터하여 4개 contract(rollback, disable, conflict, transition-audit) 모두에 대해 동일하게 검증:
  - `aggregate_identity_ref`
  - `supporting_source_message_refs`
  - `supporting_candidate_refs`
  - optional `supporting_review_refs` (initial snapshot에 있을 때)
  - 각 contract의 고유 stage 값
  - transition-audit의 `post_transition_invariants`

### 건드리지 않은 영역

- `app/serializers.py` — builder들이 이미 exact supporting refs를 올바르게 전달하고 있어 코드 변경 불필요.
- `app/handlers/aggregate.py` — lifecycle handler들이 contract refs를 덮어쓰지 않아 변경 불필요.
- `docs/NEXT_STEPS.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md` — 현재 문구가 이미 정확하여 변경 불필요.
- `e2e/`, `controller/`, `pipeline_gui/`, `pipeline_runtime/` — 이번 슬라이스 범위 밖.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_contract_refs_retained_through_lifecycle`
  - 결과: `Ran 2 tests in 5.861s`, `OK`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - 결과: `Ran 370 tests in 120.554s`, `OK`
- `git diff --check -- app/serializers.py app/handlers/aggregate.py tests/test_web_app.py docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/15` → whitespace 경고 없음
- Playwright / `make e2e-test`는 실행하지 않았습니다. 이번 슬라이스는 기존 lifecycle test의 assertion 강화만 수행했고 browser DOM/UI는 건드리지 않았기 때문입니다.

## 남은 리스크

- 새 assertion들은 serializer builder들이 exact supporting refs를 올바르게 chain-forward하는 현재 구현을 잠급니다. 미래에 supporting-ref 구조가 바뀌면 이 테스트들이 의도적으로 실패하여 변경을 드러냅니다.
- dirty working tree에 이미 존재하는 unrelated pending hunks(`controller/`, `pipeline_gui/`, `watcher_core.py`, `pipeline_runtime/` 등)는 건드리지 않았습니다.
- 이번 변경은 새 테스트 메서드를 추가하지 않고 기존 두 메서드의 assertion helper만 보강했으므로 테스트 수(370)는 변하지 않았습니다.
