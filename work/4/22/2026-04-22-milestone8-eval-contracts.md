# 2026-04-22 milestone8 eval contracts

## 변경 파일
- `core/eval_contracts.py`
- `work/4/22/2026-04-22-milestone8-eval-contracts.md`

## 사용 skill
- `finalize-lite`: handoff 필수 검증, 변경 범위, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 826
  (`milestone8_axis1_fixture_family_matrix`)에 따라 Milestone 8 Axis 1의
  manual-placeholder stage를 시작했다.
- `docs/MILESTONES.md`의 fixture-family matrix와 quality axes를 런타임 계약에서
  재사용할 수 있도록 eval 전용 module에 분리해 두되, service fixtures와 unit helpers는
  후속 slice로 남겼다.

## 핵심 변경
- `core/eval_contracts.py`를 새로 만들고 `EvalFixtureFamily` `StrEnum`에 7개 fixture
  family를 정의했다.
- `EVAL_QUALITY_AXES`에 6개 quality axis를 `frozenset[str]`로 정의했다.
- `EVAL_FIXTURE_FAMILY_AXES`에 family별 관련 quality axis mapping을 추가했다.
- `EvalArtifactCoreTrace` `TypedDict`에 eval trace artifact 공통 최소 필드를 정의했다.
- handoff 제한에 따라 `core/contracts.py`, 기존 runtime module, fixtures/loaders/helpers,
  docs, `.pipeline` control 파일은 수정하지 않았다.

## 검증
- `python3 -m py_compile core/eval_contracts.py` → 통과
- `python3 -m unittest tests.test_smoke -q` → 통과 (`Ran 150 tests`, `OK`)
- `git diff --check -- core/eval_contracts.py` → 통과

## 남은 리스크
- 이 라운드는 manual placeholder stage만 구현했다. service fixtures, unit helpers,
  loaders, e2e coverage, family-specific trace extensions는 아직 추가하지 않았다.
- `suggested_scope` value constraints는 advisory seq 825와 handoff 지시에 따라
  `EvalFixtureFamily.SCOPE_SUGGESTION_SAFETY` 기반의 후속 Milestone 8 slice로 남겼다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일과 advisory report는 이번 handoff
  범위가 아니어서 건드리지 않았다.
