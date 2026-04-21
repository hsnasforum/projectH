# 2026-04-20 autonomy key stability lock

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 좁은 회귀와 doc-sync 필요 여부만 기준으로 이번 구현 라운드의 wrap-up truth를 정리했습니다.
- `work-log-closeout`: projectH 표준 섹션 순서로 `/work` closeout을 남겼습니다.

## 변경 이유
- seq 561/564는 `classify_operator_candidate`의 per-mode default literal을 잠갔고, seq 567은 `dispatch_selection` emit payload shape를 잠갔지만, `classify_operator_candidate` 자체의 return-dict shape와 `decision_class`의 "canonical OR empty" invariant를 별도로 고정하는 테스트는 아직 없었습니다.
- 이번 라운드는 Gemini 569가 요구한 테스트 레이어의 symmetric lock만 추가해, return dict key 순서/개수 drift와 future unmapped-mode addition에서의 `decision_class` drift를 빠르게 잡는 것이 목적이었습니다.
- scope는 handoff 지시대로 정확히 한 파일, 정확히 한 메서드 추가로만 제한했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py`에 새 test method `test_classify_operator_candidate_payload_stability` 1개를 추가했습니다. 이 메서드는 `classify_operator_candidate`의 16-key return dict shape와 `decision_class` invariant를 함께 잠급니다.
- shape lock은 `shape_result = classify_operator_candidate("", control_meta={"reason_code": "truth_sync_required"}, now_ts=1_000.0)` 한 번으로 수행합니다. 여기서 `len(shape_result) == 16`과 `list(shape_result) == ["mode", "suppressed_mode", "block_reason", "reason_code", "operator_policy", "decision_class", "decision_required", "based_on_work", "based_on_verify", "classification_source", "first_seen_at", "suppress_operator_until", "operator_eligible", "publish_immediately", "routed_to", "fingerprint"]`를 고정했습니다.
- invariant lock은 5-scenario matrix로 수행합니다: `needs_operator`, `pending_operator`, `triage`, `hibernate`, `recovery`. 각 subTest는 `result["mode"] == expected_mode`를 확인한 뒤 `decision_class == "" or decision_class in SUPPORTED_DECISION_CLASSES`만 검증합니다.
- Gemini 569의 "normal mode scenario" 요청은 invariant coverage intent로 해석했고, 실제 구현에서는 `recovery`로 대체했습니다. 이유는 `classify_operator_candidate`가 `mode == "normal"`을 만들지 않기 때문입니다. `normal`은 operator candidate가 아예 없는 경우 supervisor가 `pipeline_runtime/supervisor.py:408`에서 직접 설정하며, 이 함수의 산출물이 아닙니다. 따라서 함수 범위 안에서는 `newer_unverified_work_present` + `gate_24h`로 도달 가능한 `recovery`가 "empty" half를 검증하는 올바른 substitute입니다.
- 이 새 테스트는 seq 561/564의 stricter per-mode literal test보다 의도적으로 약합니다. 기존 테스트가 각 mapped mode의 specific literal을 잠그고 있고, 이번 테스트는 future unmapped mode까지 포함해 "canonical OR empty" invariant 자체를 잠그는 역할이기 때문입니다.
- production code는 전혀 수정하지 않았습니다. `pipeline_runtime/operator_autonomy.py:331-348`의 return dict literal은 byte-for-byte 유지되며, key 순서도 그대로 확인했습니다.
- `tests/test_pipeline_runtime_supervisor.py`의 `def test_` 개수는 Gemini 569 baseline note대로 100에서 101로 늘었습니다.
- 이번 라운드에서 다른 파일은 수정하지 않았습니다. seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 / 567 contracts는 byte-for-byte 유지했고, `.pipeline/operator_request.md` seq 521 canonical literals은 seq 558 SUPERSEDES chain을 포함한 audit trail에서 그대로 보존됩니다.

## 검증
- 사전 trace 확인
  - `python3 - <<'PY' ... classify_operator_candidate('', control_meta={'reason_code':'newer_unverified_work_present','operator_policy':'gate_24h'}, now_ts=1000.0) ... PY`
  - 결과: `mode == "recovery"`, `decision_class == ""`, `list(result)` 16개 key, `len(result) == 16`
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_payload_stability`
  - 결과: `Ran 1 test in 0.001s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_defaults_decision_class_per_visible_mode`
  - 결과: `Ran 1 test in 0.000s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k classify_operator_candidate`
  - 결과: `Ran 2 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 101 tests in 0.802s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.010s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.002s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.070s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.328s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.114s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.029s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.070s`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n 'def test_classify_operator_candidate_payload_stability' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4581` 총 1건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `101`
  - `rg -n 'newer_unverified_work_present' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4620` 총 1건
  - `rg -n 'expected_keys' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `4582`, `4607` 총 2건
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py | wc -l`
    - 결과: `7`
  - `rg -n 'def test_' tests/test_operator_request_schema.py | wc -l`
    - 결과: `6`
  - `nl -ba pipeline_runtime/operator_autonomy.py | sed -n '331,348p'`
    - 결과 확인: return dict literal key 순서는 `mode`, `suppressed_mode`, `block_reason`, `reason_code`, `operator_policy`, `decision_class`, `decision_required`, `based_on_work`, `based_on_verify`, `classification_source`, `first_seen_at`, `suppress_operator_until`, `operator_eligible`, `publish_immediately`, `routed_to`, `fingerprint`로 `:332-347`에 그대로 유지됨

## 남은 리스크
- AXIS-AUTONOMY-KEY-STABILITY-LOCK은 이제 test layer에서 shipped 상태입니다. 이후 `classify_operator_candidate`의 return shape를 바꾸면 이 테스트를 의도적으로 함께 갱신해야 합니다.
- AXIS-EMIT-KEY-STABILITY-LOCK은 계속 shipped 상태입니다(seq 567).
- AXIS-STALE-REFERENCE-AUDIT는 closed 상태를 유지합니다.
- AXIS-DISPATCHER-TRACE-BACKFILL은 여전히 열린 후보이며, empirical confirmation의 가치가 계속 커지고 있습니다.
- G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree는 target 1 test file과 이 `/work` closeout 외에는 건드리지 않았습니다.
