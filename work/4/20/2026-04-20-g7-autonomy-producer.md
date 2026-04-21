# 2026-04-20 g7 autonomy producer

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `finalize-lite`: 실제로 실행한 좁은 회귀와 doc-sync 필요 여부만 기준으로 이번 구현 라운드의 wrap-up truth를 정리했습니다.
- `work-log-closeout`: projectH 표준 섹션 순서로 `/work` closeout을 남겼습니다.

## 변경 이유
- seq 549에서 `validate_operator_candidate_status`는 non-empty `decision_class`가 `SUPPORTED_DECISION_CLASSES` 밖이면 막는 defensive gate를 이미 갖고 있었지만, producer 경계인 `classify_operator_candidate`는 control meta에 literal이 없을 때 빈 문자열을 그대로 돌려주고 있었습니다.
- 이번 라운드는 Gemini 560이 좁게 고정한 producer-side slice만 구현해, 세 가지 `visible_mode`에서만 canonical `decision_class`를 채워 seq 549 gate의 producer-side counterpart를 실제로 load-bearing하게 만드는 것이 목적이었습니다.
- scope는 handoff 지시대로 `pipeline_runtime/operator_autonomy.py`의 한 블록 삽입과 `tests/test_pipeline_runtime_supervisor.py`의 direct unit test 1개 추가로 한정했습니다.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py::classify_operator_candidate`는 이제 control meta에 `decision_class` literal이 비어 있을 때만 mode-based default를 적용합니다. 매핑은 `visible_mode == "needs_operator"` → `operator_only`, `visible_mode == "triage"` → `next_slice_selection`, `visible_mode == "hibernate"` → `internal_only`입니다.
- 새 기본값 블록은 `visible_mode`와 `routed_to`가 최종 결정된 직후에 삽입되어, default된 `decision_class`가 fingerprint source와 return dict 양쪽에 동일하게 반영됩니다.
- `pending_operator`, `normal` 등 Gemini 560이 지정하지 않은 다른 `visible_mode`는 여전히 빈 문자열 default를 유지합니다. 이것은 narrow-scope decision이며 future slice에서 concrete use-case가 생길 때만 넓히면 됩니다.
- `tests/test_pipeline_runtime_supervisor.py`에는 `SUPPORTED_DECISION_CLASSES`와 `classify_operator_candidate`를 직접 import하는 line 1개와, `test_classify_operator_candidate_defaults_decision_class_per_visible_mode` 1개만 추가했습니다. 이 test는 full supervisor fixture 없이 direct unit test로 세 시나리오를 구성합니다.
- 테스트 fixture의 `reason_code`는 `_REASON_BEHAVIOR` routing을 읽고 실제로 target `visible_mode`를 만들도록 골랐습니다: `truth_sync_required` → `needs_operator`, `slice_ambiguity` → `triage`, `waiting_next_control` → `hibernate`. 각 subTest는 `result["mode"]`도 함께 확인해 chosen scenario가 의도한 visible mode를 실제로 만들었는지 검증합니다.
- AXIS-STALE-REFERENCE-AUDIT는 Gemini 560 기준으로 category-A fix-needed hit 0건이라 audit-closed로 기록만 남겼고, 이번 라운드에서는 docs file을 추가하지 않았습니다. closure는 seq 558-559-560-561 audit trail과 이 `/work` note에만 남깁니다.
- 이번 라운드에서 다른 파일은 수정하지 않았습니다. seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 contracts는 byte-for-byte 유지했고, `.pipeline/operator_request.md` seq 521 canonical literals은 SUPERSEDES chain을 포함한 audit trail에서 그대로 보존됩니다. `scripts/pipeline_runtime_gate.py`도 건드리지 않았습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_defaults_decision_class_per_visible_mode`
  - 결과: `Ran 1 test in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 99 tests in 0.615s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.012s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.003s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.083s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 8.570s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.105s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.026s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.067s`, `OK`
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n 'def classify_operator_candidate' pipeline_runtime/operator_autonomy.py`
    - 결과: `215` 총 1건
  - `rg -n 'decision_class = "(operator_only|next_slice_selection|internal_only)"' pipeline_runtime/operator_autonomy.py`
    - 결과: `308`, `310`, `312` 총 3건
  - `rg -n 'if not decision_class:' pipeline_runtime/operator_autonomy.py`
    - 결과: `306` 총 1건
  - `rg -n 'SUPPORTED_DECISION_CLASSES' pipeline_runtime/operator_autonomy.py`
    - 결과: `53` 총 1건
  - `rg -n 'classify_operator_candidate|SUPPORTED_DECISION_CLASSES' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `13`, `4511`, `4532`, `4539` 총 4건
  - `rg -n 'def test_classify_operator_candidate_defaults_decision_class_per_visible_mode' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4511` 총 1건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `99`
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py | wc -l`
    - 결과: `7`
  - `rg -n 'def test_' tests/test_operator_request_schema.py | wc -l`
    - 결과: `6`
  - `rg -n 'candidate_count|latest_any' pipeline_runtime/schema.py`
    - 결과: 총 0건

## 남은 리스크
- G7-AUTONOMY-PRODUCER는 `classify_operator_candidate` producer boundary에서 3개 mapped mode에 대해서만 부분적으로 닫혔습니다. `pending_operator`와 기타 mode는 빈 문자열 default를 유지하며, concrete use-case가 생기면 future slice에서 확장할 수 있습니다.
- AXIS-STALE-REFERENCE-AUDIT는 Gemini 560 기준 category-A hit 0건으로 closed입니다. category-B 3건(`tests/test_pipeline_runtime_schema.py:403`, `:432`, `:478`)은 intentional None-path fixture라 그대로 남습니다.
- AXIS-DISPATCHER-TRACE-BACKFILL은 여전히 열린 후보입니다.
- AXIS-EMIT-KEY-STABILITY-LOCK도 여전히 열린 후보입니다.
- G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree는 target 2 source file과 이 `/work` closeout 외에는 건드리지 않았습니다.
