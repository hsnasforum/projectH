# 2026-04-22 fixture loader scope suggestion

## 변경 파일
- `eval/fixture_loader.py`
- `data/eval/fixtures/scope_suggestion_safety_001.json`
- `work/4/22/2026-04-22-fixture-loader-scope-suggestion.md`

## 사용 skill
- `finalize-lite`: handoff 필수 검증, 변경 범위, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 835
  (`milestone8_axis3_fixture_loader_scope_fixture`)에 따라 Milestone 8을 service fixture에서
  unit helper stage로 한 단계 진전시켰다.
- Advisory seq 834 중 `eval/fixture_loader.py`와
  `data/eval/fixtures/scope_suggestion_safety_001.json`만 이번 slice로 구현하고,
  `CandidateReviewSuggestedScope` enum과 storage enforcement는 valid value 정의가 없어
  deferred로 남겼다.

## 핵심 변경
- `eval/fixture_loader.py`를 새로 추가해 fixture JSON을 이름으로 읽고
  `EvalArtifactCoreTrace` shape, `EvalFixtureFamily`, family별 expected axes,
  known quality axes를 검증하도록 했다.
- 기존 `correction_reuse_001` fixture가 loader로 읽히는지 확인 가능한 standalone
  `load_fixture()` helper를 추가했다.
- `scope_suggestion_safety_001.json` fixture를 추가하고 family axes를
  `scope_safety`, `trace_completeness`로 맞췄다.
- handoff 제한에 따라 `eval/__init__.py`, `eval/harness.py`, `core/contracts.py`,
  `core/eval_contracts.py`, `storage/session_store.py`, `.pipeline` control 파일은 수정하지 않았다.

## 검증
- `python3 -m py_compile eval/fixture_loader.py` → 통과
- `python3 -c "from eval.fixture_loader import load_fixture; d = load_fixture('correction_reuse_001'); assert d['fixture_family'] == 'correction_reuse'; print('OK')"` → 통과 (`OK`)
- `python3 -c "from eval.fixture_loader import load_fixture; d = load_fixture('scope_suggestion_safety_001'); assert d['fixture_family'] == 'scope_suggestion_safety'; print('OK')"` → 통과 (`OK`)
- `python3 -m unittest tests.test_smoke -q` → 통과 (`Ran 150 tests`, `OK`)
- `git diff --check -- eval/fixture_loader.py` → 통과

## 남은 리스크
- `eval/fixture_loader.py`는 standalone module이며 package-level export는 handoff 지시에 따라
  추가하지 않았다.
- fixture loader의 broader unit tests, additional fixture families,
  `CandidateReviewSuggestedScope` enum, storage enforcement는 이번 handoff 범위가 아니어서
  구현하지 않았다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일과 advisory report는 이번 handoff
  범위가 아니어서 건드리지 않았다.
