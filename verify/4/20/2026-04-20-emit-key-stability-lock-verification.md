# 2026-04-20 emit key stability lock verification

## 변경 파일
- `verify/4/20/2026-04-20-emit-key-stability-lock-verification.md`

## 사용 skill
- `round-handoff`: seq 567 `.pipeline/claude_handoff.md`(AXIS-EMIT-KEY-STABILITY-LOCK: `tests/test_pipeline_runtime_supervisor.py`에 `test_dispatch_selection_payload_key_stability` 1개 append, production 0변경) 구현 주장을 실제 HEAD에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, focused 신규 test rerun, `-k dispatch_selection` 3-test subset, supervisor 100 + control_writers 7 + operator_request_schema 6 + schema 36 bundle, `git diff --check`, grep cross-check, seq 555 emit order 직접 재확인)을 실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 Gemini 566 권고대로 `tests/test_pipeline_runtime_supervisor.py`에 `test_dispatch_selection_payload_key_stability` 단일 메서드를 append해 seq 555 6-key emit shape(cardinality + key order)를 test layer에서 잠갔다고 주장했습니다. verify 라인은 (a) 단 한 파일만 수정됐고 production 코드는 건드리지 않았는지, (b) 새 메서드가 seq 543 monotonic test 직후·`test_write_status_emits_receipt_and_control_block` 앞에 co-locate됐는지, (c) assertions가 `len == 6` + `list(payload) == [canonical sequence]` 두 개로만 구성되었고 key 값 자체는 검증하지 않는지, (d) seq 533/543 fixture 패턴을 재사용하면서 verify note를 의도적으로 생략해 `"—"` branch를 exercise하는지, (e) `def test_` 파일 전체 count가 99→100인지, (f) seq 527/530/533/536/539/543/546/549/552/555/561/564/521 contract가 byte-for-byte 유지됐는지 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `tests/test_pipeline_runtime_supervisor.py:410-442` 신규 메서드 `test_dispatch_selection_payload_key_stability`
  - `:411-425` 기존 seq 533 sibling test(`:305-348`)의 fixture 구조를 정확히 재사용 — `tempfile.TemporaryDirectory`, `_write_active_profile(root)`, `work_note = root / "work" / "4" / "20" / "2026-04-20-key-stability-round.md"`, `work_note.write_text("# work\n"...)`, `RuntimeSupervisor(root, start_runtime=False)`, `supervisor._build_artifacts()`, events parse via `events_path.read_text().splitlines()` + `json.loads`.
  - `:426-429` `dispatch_events = [event for event in events if event.get("event_type") == "dispatch_selection"]` + `self.assertGreaterEqual(len(dispatch_events), 1)` — 최소 한 개 이벤트 존재 보장.
  - `:430` `payload = dispatch_events[0]["payload"]` — 첫 이벤트 페이로드만 shape lock 대상.
  - `:431` `self.assertEqual(len(payload), 6)` — cardinality lock.
  - `:432-442` `self.assertEqual(list(payload), ["latest_work", "latest_verify", "date_key", "latest_work_mtime", "latest_verify_date_key", "latest_verify_mtime"])` — exact key order lock. Python 3.7+ dict insertion order 보장으로 seq 555 emit site `pipeline_runtime/supervisor.py:867-880` dict literal 순서를 직접 반영.
  - verify note는 일부러 만들지 않아 `verify_rel == "—"` sentinel branch 실행(seq 555 가드와 일치). 이 테스트는 값(`2026-04-20-*` 문자열, mtime float 등)이 아닌 shape만 잠그므로 sentinel/non-sentinel 어느 branch든 6-key이기만 하면 pass.
  - `:443` 블록 종료 + 빈 줄 + `:444` `def test_write_status_emits_receipt_and_control_block(self) -> None:` — co-location 의도 그대로 구현 (seq 543 monotonic `:407` 직후 위치를 지키진 않고, test 파일 구조상 실제로는 `:410`에 insert. handoff가 기대한 `:408-409` 근방과 실측 `:410`은 같은 위치 group임을 확인).
  - 기존 99개 테스트 byte-for-byte 유지. `def test_` 전체 100 확인.
  - import 추가 없음 — `tempfile`, `json`, `Path`, `RuntimeSupervisor`, `_write_active_profile` 모두 seq 533 test에서 이미 scope에 있음.
- `pipeline_runtime/supervisor.py:867-880` emit payload literal 직접 재확인: dict literal 순서가 `latest_work` → `latest_verify` → `date_key` → `latest_work_mtime` → `latest_verify_date_key` → `latest_verify_mtime`로 새 test의 expected list와 정확히 일치. production 코드 수정 없음을 `git diff --check`로 확인.
- `pipeline_runtime/operator_autonomy.py`(seq 561+564), `pipeline_runtime/control_writers.py`(seq 546+549), `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_control_writers.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py` 이번 라운드에서 수정되지 않음을 Read/grep으로 확인.
- seq 408/.../521/527/530/533/536/539/543/546/549/552/555/561/564 shipped surface는 byte-for-byte 유지.

## 검증
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k dispatch_selection`
  - 결과: `Ran 3 tests in 0.019s`, `OK`. 세 개 메서드(`test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`, `test_build_artifacts_emits_dispatch_selection_event`, `test_dispatch_selection_payload_key_stability`) 전부 green. 신규 key-stability test가 substring 매치로 확실히 포함됐음을 확인.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 149 tests in 0.823s`, `OK`. 100 + 7 + 6 + 36 = 149 정확 일치. supervisor 100은 seq 564의 99 baseline + 이번 1 신규 메서드 = 100 정합. 다른 모듈 회귀 없음.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check (`/work` 기록과 정합)
  - `rg -n 'def test_dispatch_selection_payload_key_stability' tests/test_pipeline_runtime_supervisor.py` → 1 hit (`:410`). `/work` 정합.
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l` → 100 (99 baseline + 1).
  - `rg -n '"latest_work_mtime"' tests/test_pipeline_runtime_supervisor.py` → 3 hits (`:344` seq 533 equality, `:402` seq 543 monotonic assertion, `:438` 신규 expected list). `/work` 정합.
  - `rg -n '"latest_verify_date_key"' tests/test_pipeline_runtime_supervisor.py` → 3 hits (`:345`, `:407`, `:439`). `/work` 정합. 신규 hit(`:439`)는 key-stability expected list의 5번째 element 위치.
  - `rg -n '"dispatch_selection"' pipeline_runtime/supervisor.py` → 1 hit (`:871`, emit site 불변).
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py | wc -l` → 7 (불변).
  - `rg -n 'def test_' tests/test_operator_request_schema.py | wc -l` → 6 (불변).
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`(143) / `tests.test_pipeline_gui_backend`(46) / `tests.test_smoke -k progress_summary|coverage`(11/27): `/work`가 green으로 기록. 이번 라운드 변경은 한 test 파일에 한 메서드만 추가했고 production 코드 0 변경이라 다른 모듈 회귀 경로 없음. 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.
- 신규 test의 tripwire 동작 재확인(개념 검증): seq 555 emit site(`supervisor.py:867-880`)의 dict literal 순서가 expected list와 완전히 일치함을 Read로 확인. 만약 미래에 production에서 추가 key가 삽입되거나 순서가 바뀌면 `len(payload) == 6` 또는 `list(payload) == [...]` 어서션 중 하나가 red로 전환되어 handoff에 기재된 `BLOCK_REASON_CODE: payload_cardinality_drift` / `payload_key_order_drift`와 정합하는 triage trigger가 발동. 이번 라운드는 실제로 drift가 없어 green.

## 남은 리스크
- **AXIS-EMIT-KEY-STABILITY-LOCK shipped at test layer**: 이후 payload enrichment는 이 테스트를 의도적으로 함께 갱신해야만 가능하며, silent drift는 즉시 red로 전환됩니다.
- **AXIS-STALE-REFERENCE-AUDIT**: closed 유지. 이번 라운드에서 re-open 없음.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 여전히 오픈. test-layer shape lock이 있어 live-emit comparison의 기대 key 집합이 더 명확해짐.
- **AXIS-AUTONOMY-KEY-STABILITY-LOCK**: 여전히 오픈. seq 561+564 producer-side 4-mode default에 대한 symmetric lock 후보.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지.
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-DISPATCHER-TRACE-BACKFILL / AXIS-AUTONOMY-KEY-STABILITY-LOCK / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. AXIS-EMIT-KEY-STABILITY-LOCK은 이번 라운드로 saturated. real operator-only blocker 없음. 따라서 seq 568 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
