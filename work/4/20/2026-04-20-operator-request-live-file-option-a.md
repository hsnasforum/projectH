# 2026-04-20 operator_request live file option a

## 변경 파일
- `tests/test_operator_request_schema.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 검증, doc-sync 필요 여부, `/work` closeout readiness만 묶어 구현 라운드를 마감했습니다.

## 변경 이유
- seq 510까지 `tests/test_operator_request_schema.py`는 self-contained `FIXTURE_HEADER`만 검증하고 있어서, 실제 repo-root `.pipeline/operator_request.md`의 drift를 advisory-mode로 감지하지 못했습니다.
- 이번 슬라이스는 live control slot을 직접 truth-sync하지 않고, stale `REASON_CODE` drift가 있으면 `skipTest`로 기록만 남기고 commit은 green으로 유지하는 option A를 적용하는 것이 목적이었습니다.

## 핵심 변경
- `tests/test_operator_request_schema.py:2`에 `from pathlib import Path`를 stdlib import block의 `import re`와 `import unittest` 사이에 추가했습니다.
- `tests/test_operator_request_schema.py:77-86`에 새 6번째 test method `test_live_operator_request_header_canonical`를 `test_decision_class_is_canonical` 바로 뒤에 추가했습니다.
- 새 테스트가 쓰는 Path resolution은 정확히 `Path(__file__).parent.parent / ".pipeline" / "operator_request.md"`입니다. path sanity one-shot은 `/home/xpdlqj/code/projectH/.pipeline/operator_request.md True`를 출력했습니다.
- 새 테스트의 contract는 다음과 같습니다.
  - file absent면 `self.skipTest("operator_request.md not present")`
  - live header의 `REASON_CODE`가 canonical set 바깥이면 `self.skipTest(f"Live file drift detected: REASON_CODE={reason_code!r}")`
  - 그 외에는 `OPERATOR_POLICY`와 `DECISION_CLASS`를 canonical frozenset에 대해 `assertIn`
- 5개의 기존 test method, `FIXTURE_HEADER`, `_parse_operator_request_header`는 byte-for-byte unchanged 상태로 유지했습니다.
- `pipeline_runtime/operator_autonomy.py`, `scripts/pipeline_runtime_gate.py`, `pipeline_runtime/control_writers.py`, `.pipeline/operator_request.md`, `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py`는 이번 라운드에서 수정하지 않았습니다.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510 shipped surfaces는 의도적으로 더 수정하지 않았습니다.
- doc-sync triage 결과 없음: 이번 변경은 advisory test widening만 포함했고, production contract나 docs 문구를 바꾸지 않았습니다.

## 검증
- grep 확인
  - `rg -n '^from pathlib import Path' tests/test_operator_request_schema.py`
    - 결과: 1건 (`:2`)
  - `rg -n 'def test_live_operator_request_header_canonical' tests/test_operator_request_schema.py`
    - 결과: 1건 (`:77`)
  - `rg -n 'def test_' tests/test_operator_request_schema.py`
    - 결과: 6건 (`:37`, `:53`, `:62`, `:65`, `:71`, `:77`)
  - `rg -n 'self.skipTest' tests/test_operator_request_schema.py`
    - 결과: 2건 (`:80`, `:84`)
  - `rg -n 'Live file drift detected: REASON_CODE=' tests/test_operator_request_schema.py`
    - 결과: 1건 (`:84`)
  - `rg -n '@unittest.skip' tests/test_operator_request_schema.py`
    - 결과: 0건
  - `rg -n 'FIXTURE_HEADER' tests/test_operator_request_schema.py`
    - 결과: 6건 (`:11`, `:38`, `:55`, `:63`, `:67`, `:73`)
  - `rg -n '_parse_operator_request_header\(' tests/test_operator_request_schema.py`
    - 결과: 6건 (`:25` definition, `:38`, `:63`, `:67`, `:73`, `:81`)
    - handoff 기대치는 5건이었지만, `rg`가 function definition line도 함께 잡아서 총 6건이 나왔습니다. 5개의 call/reference + 1개의 definition으로 해석하면 현재 구현과 일치합니다.
  - `rg -n 'live_file' tests/test_operator_request_schema.py`
    - 결과: 3건 (`:78`, `:79`, `:81`)
  - `rg -n 'SUPPORTED_DECISION_CLASSES' pipeline_runtime/operator_autonomy.py`
    - 결과: 1건 (`:53`)
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py`
    - 결과: 1건 (`:73`)
- path sanity
  - `python3 -c "from pathlib import Path; p = Path('tests/test_operator_request_schema.py').resolve().parent.parent / '.pipeline' / 'operator_request.md'; print(p, p.exists())"`
    - 결과: `/home/xpdlqj/code/projectH/.pipeline/operator_request.md True`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK (skipped=1)`
  - skipped message: `"Live file drift detected: REASON_CODE='advice_g5_not_bounded_first_sub_slice'"`
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_live_operator_request_header_canonical -v`
  - 결과: `skipped "Live file drift detected: REASON_CODE='advice_g5_not_bounded_first_sub_slice'"`
  - file-absent branch가 아니라 drift branch가 실제로 탔음을 확인했습니다.
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.093s`, `OK`
  - baseline confirmation: `45 / OK / skipped=0`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.024s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.074s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.073s`, `OK`
- `python3 -m py_compile tests/test_operator_request_schema.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- tests/test_operator_request_schema.py`
  - 결과: 출력 없음, 통과

## 남은 리스크
- 새 테스트는 현재 repo state에서는 의도적으로 SKIP됩니다. `.pipeline/operator_request.md` (seq 462 stale)의 `REASON_CODE`가 canonical set 밖에 있기 때문입니다. 이후 round가 이 파일을 canonical `REASON_CODE`로 truth-sync하면, 추가 test edit 없이 같은 테스트가 full run으로 전환됩니다.
- live file의 `OPERATOR_POLICY`와 `DECISION_CLASS` 값은 현재 canonical입니다(`gate_24h`, `red_test_family_scope_decision`). 지금은 `REASON_CODE` drift 때문에 skip으로 빠지지만, assertIn line은 이미 들어가 있어서 truth-sync 직후 별도 수정 없이 drift를 잡는 green-adjacent 상태입니다.
- G7-live-file option B(allowlist)와 option C(truth-sync live file)는 계속 deferred입니다. stale live control slot을 verify lane에서 직접 truth-sync하는 일은 Gemini 511 guardrail대로 별도 routing이 필요합니다.
- G7-gate-blocking은 option A가 최소 한 라운드 관찰되기 전에는 시기상조입니다.
- `normalize_decision_class` / `normalize_reason_code`는 여전히 pass-through이며, 세 literal의 runtime gating은 이번 슬라이스에서 강제되지 않았습니다.
- G3 / G6-sub2 / G6-sub3 / G8-pin / G9 / G10 / G11은 계속 deferred입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 구현 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree 파일은 single target test file 외에는 이번 라운드에서 건드리지 않았습니다.
