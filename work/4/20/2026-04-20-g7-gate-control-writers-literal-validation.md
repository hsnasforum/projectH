# 2026-04-20 g7 gate control-writers literal validation

## 변경 파일
- `pipeline_runtime/control_writers.py`
- `tests/test_pipeline_runtime_control_writers.py`

## 사용 skill
- `onboard-lite`: handoff가 고정한 owner boundary, target files, 검증 명령을 실제 repo 상태와 대조해 바로 구현 가능한 범위만 확인했습니다.
- `finalize-lite`: 실제 실행한 unittest/grep/diff 결과만 기준으로 doc-sync 필요 여부와 closeout readiness를 정리했습니다.
- `work-log-closeout`: projectH 표준 `/work` 형식에 맞춰 이번 구현 라운드 closeout을 남겼습니다.

## 변경 이유
- `validate_operator_candidate_status`는 operator-candidate status를 read-time에 검사하면서도 `classification_source`만 확인하고 `reason_code` / `operator_policy` literal 재검증은 하지 않았습니다. 같은 owner boundary 안에 이미 있는 `validate_operator_request_headers` write-time canonical-set enforcement를 read path에도 보강해 G7 gate gap을 줄일 필요가 있었습니다.
- `autonomy` dict 계약에는 `decision_class`가 들어오지 않으므로, 이번 slice에서 read-time 검증은 `SUPPORTED_REASON_CODES`와 `SUPPORTED_OPERATOR_POLICIES` 두 frozenset으로만 좁히고, `DECISION_CLASS`는 기존 `validate_operator_request_headers:58-60` write-time enforcement에 그대로 맡겼습니다.
- Gemini 545의 의도는 유지하되, 테스트 위치는 `tests/test_operator_request_schema.py`가 아니라 실제 `validate_operator_candidate_status` home인 `tests/test_pipeline_runtime_control_writers.py`로 바로잡아야 했습니다.

## 핵심 변경
- [control_writers.py](/home/xpdlqj/code/projectH/pipeline_runtime/control_writers.py#L228) `validate_operator_candidate_status`에 `normalize_reason_code(...)` + `SUPPORTED_REASON_CODES` membership 검사를 추가했습니다. normalized 값이 non-empty인데 canonical set 밖이면 `ValueError("unsupported reason_code: ...")`를 올립니다.
- [control_writers.py](/home/xpdlqj/code/projectH/pipeline_runtime/control_writers.py#L255) `normalize_operator_policy(...)` + `SUPPORTED_OPERATOR_POLICIES` membership 검사를 같은 read path에 추가했습니다. normalized 값이 non-empty인데 canonical set 밖이면 `ValueError("unsupported operator_policy: ...")`를 올립니다.
- empty string으로 normalize되는 literal은 계속 통과시켜 `classification_source`가 authoritative한 기존 contract를 유지했습니다. `DECISION_CLASS`는 의도적으로 이 read path에 넣지 않았고, write-time `validate_operator_request_headers:58-60` enforcement만 유지했습니다.
- [test_pipeline_runtime_control_writers.py](/home/xpdlqj/code/projectH/tests/test_pipeline_runtime_control_writers.py#L107)에 `test_validate_operator_candidate_status_rejects_unsupported_reason_code_and_operator_policy_literals`를 1개 추가해 두 오류 메시지 경로를 함께 고정했습니다. `tests/test_operator_request_schema.py`는 수정하지 않았고 `Ran 6 / OK`를 유지했습니다.
- source edit는 handoff가 허용한 두 파일에만 한정했습니다. `scripts/pipeline_runtime_gate.py`는 건드리지 않았고, seq 527 / 530 / 533 / 536 / 539 / 543 contract, `.pipeline/operator_request.md` seq 521 canonical literals, 그리고 seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486/489/495/498/501/504/507/510/513/516/517/518/519/520/521/527/530/533/536/539/543 shipped surfaces는 더 건드리지 않았습니다.
- UI, approval payload shape, agent/skill/config surface는 바뀌지 않아 이번 라운드 doc-sync는 필요하지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 6 tests in 0.008s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers.ControlWritersTest.test_validate_operator_candidate_status_rejects_unsupported_reason_code_and_operator_policy_literals`
  - 결과: `Ran 1 test in 0.001s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 98 tests in 0.713s`, `OK`
  - handoff의 `95-97` 기대보다 dirty worktree 기준 실제 baseline이 98이었지만 새로운 red는 없었습니다.
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.076s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.317s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.086s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.020s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.070s`, `OK`
- `git diff --check -- pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n 'def validate_operator_candidate_status' pipeline_runtime/control_writers.py`
    - 결과: `228` 총 1건
  - `rg -n 'unsupported reason_code|unsupported operator_policy' pipeline_runtime/control_writers.py`
    - 결과: `52`, `56`, `254`, `260` 총 4건
  - `rg -n 'SUPPORTED_REASON_CODES|SUPPORTED_OPERATOR_POLICIES' pipeline_runtime/control_writers.py`
    - 결과: `7`, `8`, `51`, `55`, `172`, `253`, `258` 총 7건
    - handoff 예상 4건과 다르게 import 2건(`:7`, `:8`)과 기존 `validate_implement_blocked_fields` reason-code check(`:172`)가 함께 잡혔습니다. 이번 slice의 새 read-time checks는 `:253`, `:258`입니다.
  - `rg -n 'def test_validate_operator_candidate_status' tests/test_pipeline_runtime_control_writers.py`
    - 결과: `78`, `107` 총 2건
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py`
    - 결과: 총 6건
  - `rg -n 'def test_' tests/test_operator_request_schema.py`
    - 결과: 총 6건
  - `rg -n 'not_a_real_reason_code_literal|not_a_real_policy_literal' tests/test_pipeline_runtime_control_writers.py`
    - 결과: `119`, `136` 총 2건
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 총 0건
  - `rg -n 'date_key' pipeline_runtime/schema.py`
    - 결과: `290`, `291`, `293` 총 3건
  - `rg -n 'dispatch_selection' pipeline_runtime/supervisor.py`
    - 결과: `865` 총 1건
  - `python3 -c 'from pipeline_runtime.operator_autonomy import SUPPORTED_REASON_CODES; print(len(SUPPORTED_REASON_CODES))'`
    - 결과: `21`

## 남은 리스크
- G7 gate blocking은 이번 라운드로 일부 닫혔습니다. read path에서는 `REASON_CODE` + `OPERATOR_POLICY` canonical-set 검증이 추가됐고, `DECISION_CLASS`는 `autonomy` dict가 그 값을 carry하기 시작할 때 future slice에서 read path로 확장할 수 있습니다. 현재는 `validate_operator_request_headers:58-60` write-time enforcement만 truth입니다.
- AXIS-STALE-REFERENCE-AUDIT는 여전히 열린 후보입니다.
- G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 defer 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0입니다. 이번 라운드는 production validation + unit test slice였습니다.
- broad dirty worktree는 그대로 두었고, 이번 라운드 source edit는 target 2파일만 건드렸습니다. `.pipeline` control files와 `scripts/pipeline_runtime_gate.py`는 untouched 상태를 유지했습니다.
