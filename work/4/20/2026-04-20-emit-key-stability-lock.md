# 2026-04-20 emit key stability lock

## 변경 파일
- `tests/test_pipeline_runtime_supervisor.py`

## 사용 skill
- `finalize-lite`: 실제 실행한 좁은 회귀와 doc-sync 필요 여부만 기준으로 이번 구현 라운드의 wrap-up truth를 정리했습니다.
- `work-log-closeout`: projectH 표준 섹션 순서로 `/work` closeout을 남겼습니다.

## 변경 이유
- seq 555의 `dispatch_selection` emit payload는 이미 6-key shape로 닫혔지만, 테스트 레이어에는 payload의 값 검증과 monotonic 검증만 있고 key 개수와 key 순서를 직접 잠그는 별도 tripwire는 없었습니다.
- 이번 라운드는 Gemini 566이 pin한 그대로 `tests/test_pipeline_runtime_supervisor.py`에 새 test method 1개만 추가해, future enrichment가 payload를 조용히 넓히거나 줄이거나 재정렬할 때 바로 red가 나도록 만드는 것이 목적이었습니다.
- scope는 handoff 지시대로 정확히 한 파일, 정확히 한 메서드 추가로만 제한했습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py`에 새 test method `test_dispatch_selection_payload_key_stability` 1개를 추가했습니다. 이 메서드는 seq 555의 6-key payload shape를 test layer에서 고정합니다.
- 테스트는 seq 533/543 fixture 패턴을 그대로 재사용합니다: `tempfile.TemporaryDirectory`, `_write_active_profile(root)`, `work_note` 작성, `RuntimeSupervisor(root, start_runtime=False)`, `supervisor._build_artifacts()`, `events.jsonl` parse.
- fixture에는 verify note를 만들지 않았습니다. 따라서 work-only `"—"` branch sentinel path가 그대로 실행되고, 이 새 테스트는 값이 아니라 shape만 잠급니다.
- assertion은 두 개뿐입니다: `len(payload) == 6`으로 cardinality를 고정하고, `list(payload) == ["latest_work", "latest_verify", "date_key", "latest_work_mtime", "latest_verify_date_key", "latest_verify_mtime"]`로 exact key order를 고정합니다.
- production code는 전혀 수정하지 않았습니다. `pipeline_runtime/supervisor.py:870-879`의 seq 555 emit payload는 byte-for-byte 유지되며, canonical key order는 `:873-878`에서 그대로 확인했습니다.
- `tests/test_pipeline_runtime_supervisor.py`의 `def test_` 개수는 Gemini 566 baseline note대로 99에서 100으로 늘었습니다.
- 이번 라운드에서 다른 파일은 수정하지 않았습니다. seq 527 / 530 / 533 / 536 / 539 / 543 / 546 / 549 / 552 / 555 / 561 / 564 contracts는 byte-for-byte 유지했고, `.pipeline/operator_request.md` seq 521 canonical literals은 seq 558 SUPERSEDES chain을 포함한 audit trail에서 그대로 보존됩니다.

## 검증
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_dispatch_selection_payload_key_stability`
  - 결과: `Ran 1 test in 0.005s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 5 tests in 0.069s`, `OK`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k dispatch_selection`
  - 결과: `Ran 3 tests in 0.030s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 100 tests in 0.751s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.007s`, `OK`
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_schema`
  - 결과: `Ran 36 tests in 0.074s`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 143 tests in 7.328s`, `OK`
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 46 tests in 0.096s`, `OK`
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.024s`, `OK`
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.071s`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, 통과
- grep 결과
  - `rg -n 'def test_dispatch_selection_payload_key_stability' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `410` 총 1건
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l`
    - 결과: `100`
  - `rg -n '"latest_work_mtime"' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `344`, `402`, `438` 총 3건
  - `rg -n '"latest_verify_date_key"' tests/test_pipeline_runtime_supervisor.py`
    - 결과: `345`, `407`, `439` 총 3건
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py | wc -l`
    - 결과: `7`
  - `rg -n 'def test_' tests/test_operator_request_schema.py | wc -l`
    - 결과: `6`
  - `rg -n '"dispatch_selection"' pipeline_runtime/supervisor.py`
    - 결과: `871` 총 1건
  - `nl -ba pipeline_runtime/supervisor.py | sed -n '842,884p'`
    - 결과 확인: emit payload key 순서는 `latest_work`, `latest_verify`, `date_key`, `latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`로 `:873-878`에 그대로 유지됨

## 남은 리스크
- AXIS-EMIT-KEY-STABILITY-LOCK은 이제 test layer에서 shipped 상태입니다. 이후 payload enrichment가 필요하면 이 테스트를 의도적으로 함께 갱신해야 하며, silent drift에 대해서는 명확한 tripwire가 생겼습니다.
- AXIS-STALE-REFERENCE-AUDIT는 closed 상태를 유지합니다.
- AXIS-DISPATCHER-TRACE-BACKFILL은 여전히 열린 후보입니다. 이제 test-layer shape lock이 생겨 live-emit comparison chain이 기대 key 집합을 더 직접적으로 cross-reference할 수 있습니다.
- AXIS-AUTONOMY-KEY-STABILITY-LOCK은 여전히 열린 후보입니다.
- G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3는 계속 deferred 상태입니다.
- unrelated `tests.test_web_app`의 `LocalOnlyHTTPServer` PermissionError 10건은 이번 범위 밖이라 그대로 남아 있습니다.
- 오늘(2026-04-20) docs-only round count는 0을 유지합니다.
- dirty worktree는 target 1 test file과 이 `/work` closeout 외에는 건드리지 않았습니다.
