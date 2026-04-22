# 2026-04-22 remaining eval service fixtures

## 변경 파일
- `data/eval/fixtures/approval_friction_001.json`
- `data/eval/fixtures/reviewed_vs_unreviewed_trace_001.json`
- `data/eval/fixtures/rollback_stop_apply_001.json`
- `data/eval/fixtures/conflict_defer_trace_001.json`
- `data/eval/fixtures/explicit_vs_save_support_001.json`
- `work/4/22/2026-04-22-remaining-eval-service-fixtures.md`

## 사용 skill
- `finalize-lite`: handoff 필수 검증, 변경 범위, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 837
  (`milestone8_axis4_remaining_service_fixtures`)에 따라 Milestone 8 service fixture
  set의 남은 5개 family를 추가했다.
- 기존에 committed 된 `correction_reuse_001`, `scope_suggestion_safety_001`에 더해
  `EvalFixtureFamily`의 7개 family가 모두 최소 JSON fixture를 갖도록 맞췄다.

## 핵심 변경
- `approval_friction_001.json`을 추가하고 axes를 `approval_friction`,
  `trace_completeness`로 맞췄다.
- `reviewed_vs_unreviewed_trace_001.json`을 추가하고 axes를 `reviewability`,
  `trace_completeness`로 맞췄다.
- `rollback_stop_apply_001.json`을 추가하고 axes를 `rollbackability`,
  `trace_completeness`로 맞췄다.
- `conflict_defer_trace_001.json`을 추가하고 axes를 `reviewability`,
  `rollbackability`, `trace_completeness`로 맞췄다.
- `explicit_vs_save_support_001.json`을 추가하고 axes를 `approval_friction`,
  `trace_completeness`로 맞췄다.
- handoff 제한에 따라 Python source, `eval/fixture_loader.py`,
  `core/eval_contracts.py`, `core/contracts.py`, `.gitignore`, `.pipeline` control 파일은
  수정하지 않았다.

## 검증
- `python3 -c "from eval.fixture_loader import load_fixture; names=['approval_friction_001','reviewed_vs_unreviewed_trace_001','rollback_stop_apply_001','conflict_defer_trace_001','explicit_vs_save_support_001']; [load_fixture(n) for n in names]; print('all 5 OK')"` → 통과 (`all 5 OK`)
- `python3 -m unittest tests.test_smoke -q` → 통과 (`Ran 150 tests`, `OK`)
- `git diff --check` → 통과

## 남은 리스크
- 이 라운드는 service fixture set 완성만 다뤘다. `CandidateReviewSuggestedScope` enum,
  storage enforcement, package-level loader export, broader fixture unit tests는 handoff 범위가
  아니어서 구현하지 않았다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일은 이번 handoff 범위가 아니어서
  건드리지 않았다.
