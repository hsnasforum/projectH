# 2026-04-20 g7 autonomy producer extend verification

## 변경 파일
- `verify/4/20/2026-04-20-g7-autonomy-producer-extend-verification.md`

## 사용 skill
- `round-handoff`: seq 564 `.pipeline/claude_handoff.md`(AXIS-G7-AUTONOMY-PRODUCER-EXTEND: `classify_operator_candidate` default block에 `pending_operator` → `operator_only` 매핑 + seq 561 test 시나리오 리스트에 pending_operator 튜플 append) 구현 주장을 실제 HEAD에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, focused seq 561/564 test rerun, supervisor 99 + control_writers 7 + operator_request_schema 6 + schema 36 bundle, `git diff --check`, 직접 trace 재현)을 실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 Gemini 563 권고대로 `pipeline_runtime/operator_autonomy.py:classify_operator_candidate`의 seq 561 default block에 `pending_operator` → `operator_only` 매핑 1개를 추가하고, `tests/test_pipeline_runtime_supervisor.py`의 seq 561 test 시나리오 리스트에 `{"reason_code": "safety_stop", "operator_policy": "gate_24h"}` 튜플을 append했다고 주장했습니다. verify 라인은 (a) 새 `elif` 분기가 `needs_operator` 직후·`triage` 앞에 insert되어 operator-facing 두 매핑이 인접한지, (b) 4번째 매핑 `operator_only`가 `SUPPORTED_DECISION_CLASSES` 안인지, (c) 새 scenario가 정말로 `visible_mode == "pending_operator"`를 만드는지(직접 trace), (d) seq 561 `subTest` 루프 body가 byte-for-byte 유지됐는지, (e) `def test_` 전체 count가 99 유지인지, (f) seq 527/530/533/536/539/543/546/549/552/555/561/521 contract가 보존됐는지 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `pipeline_runtime/operator_autonomy.py:306-314` seq 561 default block
  - `:306` `if not decision_class:` byte-for-byte 유지.
  - `:307-308` `if visible_mode == "needs_operator": decision_class = "operator_only"` 유지.
  - `:309-310` 신규 `elif visible_mode == "pending_operator": decision_class = "operator_only"` — handoff가 지정한 대로 `needs_operator`와 `triage` 사이에 insert되어 operator-facing 두 매핑이 인접.
  - `:311-312` `elif visible_mode == "triage": decision_class = "next_slice_selection"` 유지.
  - `:313-314` `elif visible_mode == "hibernate": decision_class = "internal_only"` 유지.
  - 4개 매핑의 target literal 모두 `SUPPORTED_DECISION_CLASSES`(`operator_only`, `next_slice_selection`, `internal_only`) 안에 위치. seq 549 read-time gate false-fire 없음.
  - 함수 시그니처, 다른 분기(`:215-305`, `:315-345`), return dict key 셋 모두 byte-for-byte 유지. import 추가 없음. `_REASON_BEHAVIOR`, `_IMMEDIATE_REASON_CODES`, `_GATED_REASON_CODES`, `_INTERNAL_REASON_CODES`, frozenset 정의 모두 불변.
- `tests/test_pipeline_runtime_supervisor.py:4511-4545` seq 561 test 확장
  - `:4511` 메서드 정의(`test_classify_operator_candidate_defaults_decision_class_per_visible_mode`) byte-for-byte 유지.
  - `:4512-4533` scenarios 리스트가 3→4 tuple로 확장. 기존 3 tuple(`needs_operator`/`triage`/`hibernate`)은 byte-for-byte 유지, `:4528-4532` 위치에 신규 4번째 tuple `("pending_operator", {"reason_code": "safety_stop", "operator_policy": "gate_24h"}, "operator_only")` append.
  - `:4535-4545` subTest loop body(`for expected_mode, control_meta, expected_decision_class in scenarios:` + `with self.subTest(mode=expected_mode):` + 3개 어서션)가 byte-for-byte 유지. handoff 요구 정합.
  - `:13` seq 561 import 라인(`from pipeline_runtime.operator_autonomy import (SUPPORTED_DECISION_CLASSES, classify_operator_candidate,)`) 이미 존재해 재추가 없음.
  - 파일의 `def test_` 총 수는 99 유지 (subTest 확장은 같은 메서드 안이라 count 변화 없음).
- `pipeline_runtime/control_writers.py`, `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_control_writers.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py` 이번 라운드에서 수정되지 않음을 Read/grep으로 확인.
- seq 408/.../521/527/530/533/536/539/543/546/549/552/555/561 shipped surface는 byte-for-byte 유지.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- 직접 trace 재현 (`python3 -c "from pipeline_runtime.operator_autonomy import classify_operator_candidate; r = classify_operator_candidate('', control_meta={'reason_code': 'safety_stop', 'operator_policy': 'gate_24h'}, now_ts=1000.0); print('mode=', r['mode'], 'decision_class=', r['decision_class'])"`)
  - 결과: `mode= pending_operator decision_class= operator_only`. scenario가 정말로 `pending_operator`를 생성하고 새 default block이 load-bearing함을 직접 증명.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_defaults_decision_class_per_visible_mode`
  - 결과: `Ran 1 test in 0.001s`, `OK`. 4 subTest 전부 green.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 148 tests in 0.876s`, `OK`. 99 + 7 + 6 + 36 = 148 정확 일치. seq 549 read-time gate가 새 default literal `operator_only`를 canonical set 안으로 인식해 red 없이 통과.
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check (`/work` 기록과 직접 대조)
  - `rg -n 'if not decision_class:' pipeline_runtime/operator_autonomy.py` → 1 hit (`:306`). `/work` 정합.
  - `rg -n 'decision_class = "(operator_only|next_slice_selection|internal_only)"' pipeline_runtime/operator_autonomy.py` → 4 hits (`:308`, `:310`, `:312`, `:314`). `/work` 정합.
  - `rg -n 'visible_mode == "(needs_operator|pending_operator|triage|hibernate)"' pipeline_runtime/operator_autonomy.py` → 4 hits (`:307`, `:309`, `:311`, `:313`). `/work` 정합.
  - `rg -n 'pending_operator' tests/test_pipeline_runtime_supervisor.py` → 1 hit (`:4529`). `/work` 정합.
  - `rg -n 'safety_stop' tests/test_pipeline_runtime_supervisor.py` → 1 hit (`:4530`). `/work` 정합.
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l` → 99 (baseline 유지).
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`(143) / `tests.test_pipeline_gui_backend`(46) / `tests.test_smoke -k progress_summary|coverage`(11/27): `/work`가 green으로 기록. 이번 라운드 변경은 seq 561 default block에 `elif` 1개 추가 + test scenarios에 tuple 1개 추가로 한정되었고, watcher_core가 `classify_operator_candidate`를 import하긴 하지만 빈 문자열에서 canonical literal로 default되는 변경은 consumer가 빈 문자열을 특별히 요구하지 않는 이상 회귀 없음. 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **G7-AUTONOMY-PRODUCER fully closed for reachable modes**: 4개 `visible_mode`(`needs_operator`, `pending_operator`, `triage`, `hibernate`)에 canonical default 완비. `normal`이나 다른 unmapped mode는 `classify_operator_candidate`의 empty `decision_class` 경로에서 관찰되지 않거나 operator/autonomy semantic상 기본값이 필요 없는 상태. 필요 시 future slice에서 확장 가능.
- **AXIS-STALE-REFERENCE-AUDIT**: closed 유지 (이번 라운드에서 re-open 없음). category-B 3건은 intentional None-path fixture로 그대로 남음.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 여전히 오픈. live dispatcher emit이 이제 6-key shape + autonomy 경로의 canonical decision_class 4-mode까지 싣기 때문에 empirical confirmation 축이 한층 또렷.
- **AXIS-EMIT-KEY-STABILITY-LOCK**: 여전히 오픈. seq 555 6-key shape을 test layer에서 잠그는 슬라이스 후보.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지.
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-DISPATCHER-TRACE-BACKFILL / AXIS-EMIT-KEY-STABILITY-LOCK / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. G7-AUTONOMY-PRODUCER 축은 이번 라운드로 reachable mode 전체에서 saturated. real operator-only blocker도 없음. 따라서 seq 565 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
