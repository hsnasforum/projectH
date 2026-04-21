# 2026-04-20 g7 decision_class read path

## 변경 파일
- `pipeline_runtime/control_writers.py`
- `tests/test_pipeline_runtime_control_writers.py`

## 사용 skill
- `onboard-lite`: handoff, 직전 G7 `/work`·`/verify`, target owner boundary를 다시 읽고 이번 slice가 exact하게 actionable한지 확인했습니다.
- `finalize-lite`: 실제 실행한 unittest/grep/diff 결과만 기준으로 이번 라운드의 wrap-up truth와 doc-sync 필요 여부를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식으로 이번 bounded slice closeout을 남겼습니다.

## 변경 이유
- seq 546에서 `validate_operator_candidate_status` read path는 `SUPPORTED_REASON_CODES` + `SUPPORTED_OPERATOR_POLICIES` 두 frozenset만 검증했고, 세 번째 canonical set인 `SUPPORTED_DECISION_CLASSES`는 write-time `validate_operator_request_headers:58-60`에만 걸려 있었습니다.
- 이번 라운드는 같은 control-writers owner boundary 안에서 `decision_class`도 같은 read path로 대칭 추가해, read-time canonical literal enforcement를 3개 frozenset 전체로 맞추는 것이 목적이었습니다.
- 현재 `autonomy` dict 계약은 `decision_class`를 필수로 carry하지 않으므로, 새 검사는 normalized 값이 non-empty일 때만 load-bearing하고 empty pass-through는 그대로 유지해야 했습니다.

## 핵심 변경
- [control_writers.py](/home/xpdlqj/code/projectH/pipeline_runtime/control_writers.py#L6)에 기존 `from .operator_autonomy import (...)` 블록만 확장해 `SUPPORTED_DECISION_CLASSES`를 추가했습니다. 새로운 `import` statement는 만들지 않았습니다.
- [control_writers.py](/home/xpdlqj/code/projectH/pipeline_runtime/control_writers.py#L229) `validate_operator_candidate_status`에 `decision_class = str(autonomy.get("decision_class") or "").strip()` 1줄을 추가했고, 기존 `reason_code` / `operator_policy` read-time 검사 바로 뒤에 `normalize_decision_class(...) + SUPPORTED_DECISION_CLASSES` membership block을 덧붙였습니다.
- 새 block은 normalized `decision_class`가 non-empty인데 canonical set 밖일 때만 `ValueError("unsupported decision_class: ...")`를 올립니다. 현재 caller처럼 `decision_class`가 비어 있거나 누락된 `autonomy` dict는 계속 통과합니다.
- [test_pipeline_runtime_control_writers.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_control_writers.py#L142)에 `test_validate_operator_candidate_status_rejects_unsupported_decision_class_literal` 1건을 seq 546 sibling 바로 뒤에 append했습니다. negative-only shape로 `not_a_real_decision_class_literal`이 새 오류 메시지에 걸리는지만 고정했고, 기존 empty pass-through는 seq 546 sibling test의 두 번째 호출이 계속 담당합니다.
- `validate_operator_request_headers`의 write-time shape, `tests/test_operator_request_schema.py` 6-test surface, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, 그리고 seq 527 / 530 / 533 / 536 / 539 / 543 / 546 contracts는 byte-for-byte 유지했습니다. UI/approval/doc-sensitive surface 변경도 없어 이번 라운드 doc-sync는 필요하지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.005s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers.ControlWritersTest.test_validate_operator_candidate_status_rejects_unsupported_decision_class_literal`
  - 결과: `Ran 1 test in 0.000s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers.ControlWritersTest.test_validate_operator_candidate_status_requires_structured_classification_source`
  - 결과: `Ran 1 test in 0.000s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers.ControlWritersTest.test_validate_operator_candidate_status_rejects_unsupported_reason_code_and_operator_policy_literals`
  - 결과: `Ran 1 test in 0.001s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 98 tests in 0.757s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.104s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.423s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.134s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.040s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.098s`, `OK`
- `git diff --check -- pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n 'def validate_operator_candidate_status' pipeline_runtime/control_writers.py`
    - 결과: `229` 총 1건
    - handoff의 `:228` 예상은 새 import 1줄(`SUPPORTED_DECISION_CLASSES`) 추가로 `validate_operator_candidate_status`가 한 줄 아래로 밀리면서 `:229`가 되었습니다.
  - `rg -n 'unsupported reason_code|unsupported operator_policy|unsupported decision_class' pipeline_runtime/control_writers.py`
    - 결과: `53`, `57`, `256`, `262`, `268` 총 5건
  - `rg -n 'SUPPORTED_REASON_CODES|SUPPORTED_OPERATOR_POLICIES|SUPPORTED_DECISION_CLASSES' pipeline_runtime/control_writers.py`
    - 결과: `7`, `8`, `9`, `52`, `56`, `173`, `255`, `260`, `266` 총 9건
  - `rg -n 'normalize_decision_class' pipeline_runtime/control_writers.py`
    - 결과: `10`, `59`, `263` 총 3건
  - `rg -n 'def test_validate_operator_candidate_status' tests/test_pipeline_runtime_control_writers.py`
    - 결과: `78`, `107`, `142` 총 3건
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py`
    - 결과: 총 7건
  - `rg -n 'def test_' tests/test_operator_request_schema.py`
    - 결과: 총 6건
  - `rg -n 'not_a_real_decision_class_literal' tests/test_pipeline_runtime_control_writers.py`
    - 결과: `157` 총 1건
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 총 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건
  - `rg -n 'dispatch_selection' pipeline_runtime/supervisor.py`
    - 결과: `865` 총 1건
  - `python3 -c 'from pipeline_runtime.operator_autonomy import SUPPORTED_DECISION_CLASSES; print(len(SUPPORTED_DECISION_CLASSES))'`
    - 결과: `6`

## 남은 리스크
- G7-gate는 이번 라운드로 control-writers owner boundary에서 read-time 3개 frozenset(`SUPPORTED_REASON_CODES`, `SUPPORTED_OPERATOR_POLICIES`, `SUPPORTED_DECISION_CLASSES`) 전체를 닫았고, 기존 write-time enforcement까지 합쳐 fully closed 상태입니다. future caller가 `autonomy["decision_class"]`를 carry하기 시작해도 unsupported literal은 이제 read path에서 방어됩니다.
- 현재 `decision_class`는 `autonomy` dict에서 여전히 optional이며, 이번 라운드도 empty pass-through를 유지했습니다. 즉 지금의 caller behavior는 바뀌지 않았고, 새 검사는 future producer wiring에 대한 defensive gate 성격입니다.
- AXIS-STALE-REFERENCE-AUDIT는 여전히 열린 후보입니다.
- AXIS-EMIT-PAYLOAD-ENRICH, AXIS-DISPATCHER-TRACE-BACKFILL도 여전히 열린 후보입니다.
- G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0입니다.
- broad dirty worktree는 그대로 두었고, 이번 라운드 source edit는 target 2파일만 건드렸습니다. `.pipeline/operator_request.md` seq 521 canonical literals과 `scripts/pipeline_runtime_gate.py`는 untouched 상태를 유지했습니다.
