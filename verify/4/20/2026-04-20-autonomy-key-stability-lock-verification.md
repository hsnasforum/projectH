# 2026-04-20 autonomy key stability lock verification

## 변경 파일
- `verify/4/20/2026-04-20-autonomy-key-stability-lock-verification.md`

## 사용 skill
- `round-handoff`: seq 570 `.pipeline/claude_handoff.md`(AXIS-AUTONOMY-KEY-STABILITY-LOCK: `tests/test_pipeline_runtime_supervisor.py`에 `test_classify_operator_candidate_payload_stability` 1개 append, production 0변경) 구현 주장을 실제 HEAD에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, focused 신규 test rerun, `-k classify_operator_candidate` 2-test subset, supervisor 101 + control_writers 7 + operator_request_schema 6 + schema 36 bundle, `git diff --check`, grep cross-check, recovery scenario 직접 trace)을 실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 Gemini 569 권고대로 `tests/test_pipeline_runtime_supervisor.py`에 `test_classify_operator_candidate_payload_stability` 단일 메서드를 append해 (a) `classify_operator_candidate` return dict의 16-key shape lock과 (b) `decision_class` "canonical OR empty" invariant lock을 5-scenario matrix로 잠갔다고 주장했습니다. verify 라인은 (a) 단 한 파일만 수정됐고 production 코드는 건드리지 않았는지, (b) 16-key expected_keys 리스트가 `pipeline_runtime/operator_autonomy.py:331-348` return dict literal 순서와 완전히 일치하는지, (c) Gemini 569의 "normal mode scenario" 요구가 `recovery` mode(unmapped reachable, classify_operator_candidate scope 안)로 truthful하게 대체됐는지, (d) 5-scenario 중 recovery가 실제로 `mode=recovery, decision_class=""`를 만드는지, (e) 기존 seq 561/564 test와 중복 어서션이 없는지, (f) `def test_` 파일 전체 count가 100→101인지, (g) seq 527/530/533/536/539/543/546/549/552/555/561/564/567/521 contract가 byte-for-byte 유지됐는지 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `tests/test_pipeline_runtime_supervisor.py:4581-4639` 신규 메서드 `test_classify_operator_candidate_payload_stability`
  - `:4582-4599` `expected_keys` 리스트 (16개): `mode`, `suppressed_mode`, `block_reason`, `reason_code`, `operator_policy`, `decision_class`, `decision_required`, `based_on_work`, `based_on_verify`, `classification_source`, `first_seen_at`, `suppress_operator_until`, `operator_eligible`, `publish_immediately`, `routed_to`, `fingerprint`. `pipeline_runtime/operator_autonomy.py:332-347` 소스 순서와 완전히 일치(본 verify round에서 Read로 재확인).
  - `:4601-4607` shape lock: `shape_result = classify_operator_candidate("", control_meta={"reason_code": "truth_sync_required"}, now_ts=1_000.0)` + `assertEqual(len(shape_result), 16)` + `assertEqual(list(shape_result), expected_keys)`. Python 3.7+ dict insertion order 보장을 이용해 return dict의 16-key cardinality + exact order를 한 번에 잠금.
  - `:4609-4624` invariant scenarios(5개): `needs_operator`(truth_sync_required), `pending_operator`(safety_stop+gate_24h), `triage`(slice_ambiguity), `hibernate`(waiting_next_control), `recovery`(newer_unverified_work_present+gate_24h). 앞의 4개는 seq 561/564 매핑과 동일하지만 이 테스트는 per-mode specific literal을 잠그지 않고 약한 invariant만 잠금.
  - `:4626-4639` `subTest` 루프: `result["mode"] == expected_mode` 확인 후 `decision_class` 추출 → `assertTrue(decision_class == "" or decision_class in SUPPORTED_DECISION_CLASSES, ...)`. 4 mapped mode는 canonical, 1 unmapped(`recovery`)는 empty로 "canonical OR empty" invariant의 양쪽 반쪽을 모두 증명.
  - Gemini 569의 "normal mode scenario" 요구는 `recovery`로 대체됨. `normal`은 `pipeline_runtime/supervisor.py:408`에서 supervisor가 직접 설정하는 값이며 `classify_operator_candidate`의 산출물이 아니므로 함수 범위 안에서는 unreachable. `recovery`는 `_GATED_REASON_CODES`(`newer_unverified_work_present`)로 도달 가능한 unmapped mode로, seq 561/564 default block에 `elif`가 없어 `decision_class == ""`를 유지함(본 verify의 직접 trace로 재확인).
  - 기존 100개 테스트 byte-for-byte 유지. `def test_` 전체 101 확인. import 추가 없음 — `SUPPORTED_DECISION_CLASSES`와 `classify_operator_candidate`는 seq 561에서 `:13`에 이미 추가되어 있음.
  - 위치는 class 끝의 `test_classify_operator_candidate_defaults_decision_class_per_visible_mode`(`:4511-4545`) 직후, `if __name__ == "__main__":`(`:4642`) 앞에 co-locate됨.
- `pipeline_runtime/operator_autonomy.py:331-348` return dict literal 직접 재확인: 16개 key가 정확히 `expected_keys` 리스트와 일치. production 코드 수정 없음을 `git diff --check`로 확인.
- seq 561/564의 기존 test `test_classify_operator_candidate_defaults_decision_class_per_visible_mode`(`:4511-4545`)는 byte-for-byte 유지되며, 신규 테스트와 어서션 shape가 구분됨(seq 561/564는 per-mode specific canonical literal 잠금, 이번 seq 570은 shape + "canonical OR empty" invariant 잠금).
- `pipeline_runtime/supervisor.py`, `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/control_writers.py`, `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_control_writers.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py` 이번 라운드에서 수정되지 않음을 Read/grep으로 확인.
- seq 408/.../521/527/530/533/536/539/543/546/549/552/555/561/564/567 shipped surface는 byte-for-byte 유지.

## 검증
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- 직접 trace 재현 (`python3 -c "from pipeline_runtime.operator_autonomy import classify_operator_candidate; r = classify_operator_candidate('', control_meta={'reason_code': 'newer_unverified_work_present', 'operator_policy': 'gate_24h'}, now_ts=1000.0); print('mode=', r['mode'], 'decision_class=', repr(r['decision_class']), 'len=', len(r))"`)
  - 결과: `mode= recovery decision_class= '' len= 16`. recovery scenario가 정말로 `mode=recovery, decision_class=""` 생성하고 return dict는 정확히 16 key임을 직접 증명.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k classify_operator_candidate`
  - 결과: `Ran 2 tests in 0.001s`, `OK`. 두 메서드(`test_classify_operator_candidate_defaults_decision_class_per_visible_mode`, `test_classify_operator_candidate_payload_stability`) 전부 green. seq 561/564 회귀 + seq 570 신규 동시 확인.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 150 tests in 0.738s`, `OK`. 101 + 7 + 6 + 36 = 150 정확 일치. supervisor 101은 seq 567의 100 baseline + 이번 1 신규 메서드 = 101 정합.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check (`/work` 기록과 정합)
  - `rg -n 'def test_classify_operator_candidate_payload_stability' tests/test_pipeline_runtime_supervisor.py` → 1 hit (`:4581`). `/work` 정합.
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l` → 101 (100 baseline + 1).
  - `rg -n 'newer_unverified_work_present' tests/test_pipeline_runtime_supervisor.py` → 1 hit (`:4620`). unmapped-mode scenario가 신규 test 안에만 위치.
  - `rg -n 'expected_keys' tests/test_pipeline_runtime_supervisor.py` → 2 hits (`:4582` 정의, `:4607` 어서션).
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py | wc -l` → 7 (불변).
  - `rg -n 'def test_' tests/test_operator_request_schema.py | wc -l` → 6 (불변).
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`(143) / `tests.test_pipeline_gui_backend`(46) / `tests.test_smoke -k progress_summary|coverage`(11/27): `/work`가 green으로 기록. 이번 라운드 변경은 한 test 파일에 한 메서드만 추가했고 production 코드 0 변경이라 다른 모듈 회귀 경로 없음. 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **AXIS-AUTONOMY-KEY-STABILITY-LOCK shipped at test layer**: `classify_operator_candidate` return shape가 드러나지 않게 바뀌면 `test_classify_operator_candidate_payload_stability`가 즉시 red로 전환하고 `BLOCK_REASON_CODE: return_dict_key_order_drift` / `return_dict_cardinality_drift` / `recovery_mode_route_mismatch` 등이 triage triger가 됩니다.
- **AXIS-EMIT-KEY-STABILITY-LOCK**: 계속 shipped(seq 567). emission과 producer 양쪽의 shape lock이 이제 symmetric하게 존재.
- **AXIS-STALE-REFERENCE-AUDIT**: closed 유지.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 여전히 오픈. live emit이 6-key shape + canonical decision_class 전반을 모두 나르므로 empirical confirmation 축이 가장 또렷한 남은 후보.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지.
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-DISPATCHER-TRACE-BACKFILL / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. AXIS-EMIT-KEY-STABILITY-LOCK과 AXIS-AUTONOMY-KEY-STABILITY-LOCK 모두 saturated. real operator-only blocker도 없음. 따라서 seq 571 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
