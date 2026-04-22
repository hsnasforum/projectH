# 2026-04-22 correction reuse service fixture

## 변경 파일
- `data/eval/fixtures/correction_reuse_001.json`
- `work/4/22/2026-04-22-correction-reuse-service-fixture.md`

## 사용 skill
- `finalize-lite`: handoff 필수 검증, 변경 범위, `/work` closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 830
  (`milestone8_axis2_first_service_fixture`)에 따라 Milestone 8의 첫 service fixture
  artifact를 추가했다.
- fixture는 `core/eval_contracts.py`의 `EvalArtifactCoreTrace` 공통 필드와
  `EvalFixtureFamily.CORRECTION_REUSE` family axes
  (`correction_reuse`, `trace_completeness`)에 맞춘 수동 JSON placeholder이다.

## 핵심 변경
- `data/eval/fixtures/` 디렉터리를 만들고 `correction_reuse_001.json`을 추가했다.
- fixture에는 `artifact_id`, `session_id`, `fixture_family`, `eval_axes`,
  `trace_version`, `recorded_at`만 포함했다.
- handoff 제한에 따라 `eval/harness.py`, `core/contracts.py`, `core/eval_contracts.py`,
  Python source, loader, test helper, 추가 fixture, `.pipeline` control 파일은 수정하지 않았다.
- 현재 `.gitignore`의 `data/*` 규칙 때문에 `data/eval/fixtures/correction_reuse_001.json`은
  ignored file로 표시된다. handoff가 단일 fixture 생성만 허용했으므로 `.gitignore` 예외는
  추가하지 않았다.

## 검증
- `python3 -c "import json; d=json.load(open('data/eval/fixtures/correction_reuse_001.json')); assert d['fixture_family']=='correction_reuse'; assert set(d['eval_axes'])=={'correction_reuse','trace_completeness'}; print('OK')"` → 통과 (`OK`)
- `python3 -m unittest tests.test_smoke -q` → 통과 (`Ran 150 tests`, `OK`)
- `git diff --check -- data/eval/fixtures/correction_reuse_001.json` → 통과

## 남은 리스크
- fixture 파일은 현재 `data/*` ignore 규칙에 걸린다. 후속 verify/handoff 또는 publish 라운드가
  이 파일을 추적 대상으로 삼으려면 `.gitignore` 예외 추가 또는 `git add -f` 판단이 필요하다.
- eval fixture loader, unit helper, additional fixture, `suggested_scope` value constraints는
  이번 handoff 범위가 아니어서 구현하지 않았다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일과 advisory report는 이번 handoff
  범위가 아니어서 건드리지 않았다.
