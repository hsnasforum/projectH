# 2026-04-20 g7 autonomy producer extend

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 좁은 회귀와 doc-sync 필요 여부만 기준으로 이번 구현 라운드의 wrap-up truth를 정리했습니다.
- `work-log-closeout`: projectH 표준 섹션 순서로 `/work` closeout을 남겼습니다.

## 변경 이유
- seq 561에서 `classify_operator_candidate`의 mode-based `decision_class` default는 `needs_operator`, `triage`, `hibernate`까지만 canonical literal을 채우고 `pending_operator`는 빈 문자열로 남겨 두고 있었습니다.
- 이번 라운드는 Gemini 563이 pin한 그대로, 그 남은 reachable `visible_mode` 1개만 좁게 닫아 producer 경계의 symmetry를 맞추는 것이 목적이었습니다.
- 구현 범위는 handoff 지시대로 seq 561 default block의 `elif` 1개 추가와, 기존 `subTest` 시나리오 표에 tuple 1개 추가로만 제한했습니다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py::classify_operator_candidate`의 seq 561 default block은 이제 4개 `visible_mode`를 다룹니다: `needs_operator`, `pending_operator`, `triage`, `hibernate`. 이번 라운드 추가분은 `pending_operator` → `operator_only` 1개입니다.
- 이 4번째 매핑은 `needs_operator` → `operator_only`와 대칭입니다. 두 mode 모두 operator-facing decision이고, `pending_operator`는 24시간 suppression window 또는 internal-only routing 때문에 아직 operator-eligible이 아닐 뿐 decision class의 의미 자체는 동일합니다.
- `tests/test_pipeline_runtime_supervisor.py::test_classify_operator_candidate_defaults_decision_class_per_visible_mode`는 새 test method를 추가하지 않고, 기존 seq 561 `subTest` 시나리오 표만 3개에서 4개로 넓혔습니다. 따라서 파일의 `def test_` 개수는 그대로 99입니다.
- 4번째 시나리오는 `{"reason_code": "safety_stop", "operator_policy": "gate_24h"}`와 기존 loop의 `now_ts=1_000.0`를 그대로 사용합니다. 이 fixture가 `pending_operator`를 만드는 이유는 다음과 같습니다:
  - `operator_policy="gate_24h"`가 meta에서 바로 채택되어 classification source가 `operator_policy`가 됩니다.
  - `resolved_reason="safety_stop"`은 `_IMMEDIATE_REASON_CODES`에 속합니다.
  - `operator_policy == "gate_24h"` 분기에서 immediate reason이므로 `mode="pending_operator"`, `routed_to="codex_followup"`가 됩니다.
  - `control_mtime`를 주지 않았으므로 `first_seen_ts = now_ts = 1_000.0`이고, `suppress_until_ts = 1_000.0 + 24*3600`이 되어 `operator_eligible`은 `False`입니다.
  - 따라서 `visible_mode`는 `needs_operator`로 승격되지 않고 `pending_operator`로 남습니다.
- 이번 라운드에서는 다른 파일을 수정하지 않았습니다. seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 contracts는 byte-for-byte 유지했고, `.pipeline/operator_request.md` seq 521 canonical literals은 seq 558 SUPERSEDES chain을 포함한 audit trail에서 그대로 보존됩니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0
- 사전 trace 확인
  - `python3 - <<'PY' ... classify_operator_candidate('', control_meta={'reason_code':'safety_stop','operator_policy':'gate_24h'}, now_ts=1000.0)['mode'] ... PY`
  - 결과: `pending_operator`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_defaults_decision_class_per_visible_mode`
  - 결과: `Ran 1 test in 0.000s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 99 tests in 0.848s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.009s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.082s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.360s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.122s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.031s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.079s`, `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n 'if not decision_class:' pipeline_runtime/operator_autonomy.py`
    - 결과: `306` 총 1건
  - `rg -n 'decision_class = "(operator_only|next_slice_selection|internal_only)"' pipeline_runtime/operator_autonomy.py`
    - 결과: `308`, `310`, `312`, `314` 총 4건
  - `rg -n 'visible_mode == "(needs_operator|pending_operator|triage|hibernate)"' pipeline_runtime/operator_autonomy.py`
    - 결과: `307`, `309`, `311`, `313` 총 4건
  - `rg -n 'def classify_operator_candidate' pipeline_runtime/operator_autonomy.py`
    - 결과: `215` 총 1건
  - `rg -n 'pending_operator' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4529` 총 1건
  - `rg -n 'safety_stop' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4530` 총 1건
  - `rg -n 'def test_classify_operator_candidate_defaults_decision_class_per_visible_mode' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4511` 총 1건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `99`
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py | wc -l`
    - 결과: `7`
  - `rg -n 'def test_' tests/test_operator_request_schema.py | wc -l`
    - 결과: `6`

## 남은 리스크
- G7-AUTONOMY-PRODUCER는 이제 4개 reachable `visible_mode`(`needs_operator`, `pending_operator`, `triage`, `hibernate`)에 대해 닫혔습니다. `normal` 같은 unmapped mode는 `classify_operator_candidate`의 empty `decision_class` 경로에서 관찰되지 않았거나 별도 default가 필요하지 않은 상태입니다.
- AXIS-STALE-REFERENCE-AUDIT는 closed 상태를 유지합니다. 이번 라운드에서 re-open하지 않았습니다.
- AXIS-DISPATCHER-TRACE-BACKFILL은 여전히 열린 후보입니다.
- AXIS-EMIT-KEY-STABILITY-LOCK도 여전히 열린 후보입니다.
- G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree는 target 2 source file과 이 `/work` closeout 외에는 건드리지 않았습니다.
