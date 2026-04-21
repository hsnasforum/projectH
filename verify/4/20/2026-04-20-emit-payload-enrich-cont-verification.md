# 2026-04-20 emit payload enrich cont verification

## 변경 파일
- `verify/4/20/2026-04-20-emit-payload-enrich-cont-verification.md`

## 사용 skill
- `round-handoff`: seq 555 `.pipeline/claude_handoff.md` (AXIS-EMIT-PAYLOAD-ENRICH-CONT: `dispatch_selection` emit payload 3→6 keys 확장 + seq 533 sibling / seq 543 monotonic 테스트 동시 확장) 구현 주장을 실제 HEAD에 대조하고, handoff가 요구한 narrowest 재검증(`py_compile`, focused `-k build_artifacts`, 전체 supervisor 98, control_writers 7 / operator_request_schema 6 / schema 36, `git diff --check`, grep cross-check)을 직접 재실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 Gemini 554 권고대로 `_build_artifacts` emit payload를 6-key shape(`latest_work`, `latest_verify`, `date_key`, `latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`)로 확장하고, 두 consumer 테스트를 같은 슬라이스에서 함께 확장했다고 주장했습니다. verify 라인은 (a) 새 세 키가 지정된 순서로 append됐는지, (b) `verify_date_key` 계산이 seq 552 `work_date_key`와 대칭이고 `"—"` sentinel을 공유하는지, (c) mtime 값이 이미 scoped된 `work_mtime`/`verify_mtime` 변수 재사용인지, (d) `_build_artifacts` 반환 dict 불변인지, (e) seq 533 equality가 6-key로 커지면서 mtime 캡처 타이밍 mismatch가 없는지, (f) seq 543 additive loop가 기존 어서션을 byte-for-byte 보존한 채 세 assertion만 append했는지, (g) seq 527/530/533/536/539/543/546/549/552/521 contract가 유지됐는지를 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `pipeline_runtime/supervisor.py:864-880` `_build_artifacts` emit block
  - `:864-866` 기존 `work_date_key` derivation byte-for-byte 유지.
  - `:867-869` 신규 대칭 derivation `verify_date_key = ""` + `if verify_rel and verify_rel != "—": verify_date_key = Path(verify_rel).name[:10]`. seq 552 `work_date_key` 패턴과 정확히 동일 구조, `"—"` sentinel 공유.
  - `:870-880` `self._append_event("dispatch_selection", {...})`의 payload dict가 3-key에서 6-key로 확장됨. 키 순서: `latest_work`(`:873`), `latest_verify`(`:874`), `date_key`(`:875`), `latest_work_mtime`(`:876`), `latest_verify_date_key`(`:877`), `latest_verify_mtime`(`:878`). 기존 3-key byte-for-byte 유지, 새 3-key는 지정된 순서로 append.
  - `latest_work_mtime`은 `:843`에서 `latest_round_markdown`가 반환한 `work_mtime` 그대로 재사용. `latest_verify_mtime`은 `:845`/`:858`/`:861`/`:863`에서 branched로 세팅된 `verify_mtime` 그대로 재사용. 새 I/O 없음.
  - `:881-884` 반환 dict(`{"latest_work": {"path": work_rel, "mtime": work_mtime}, "latest_verify": {"path": verify_rel, "mtime": verify_mtime}}`) byte-for-byte 유지. `_build_artifacts` 반환 계약 불변.
  - 다른 emit site(`:1214`, `:1257`, `:1260`, `:1634`, `:1647`, `:1669`, `:1691`, `:1713`, `:1728`, `:1743`, `:1748`, `:1750`, `:1770`, `:2195`, `:2205`, `:2213`, `:2236`, `:2268`) 모두 byte-for-byte 유지 — 본 verify에서 재확인. import 추가 없음.
- `tests/test_pipeline_runtime_supervisor.py:305-348` seq 533 sibling
  - `:335-336` 신규 `expected_work_mtime = work_note.stat().st_mtime` + `expected_verify_mtime = verify_note.stat().st_mtime` (assert 직전 캡처; 파일은 `:313-317`에서 이미 작성됨).
  - `:337-347` 기존 `self.assertEqual(dispatch_events[0]["payload"], {...})` equality를 6-key로 확장: 기존 3 키(`latest_work`, `latest_verify`, `date_key="2026-04-20"`) byte-for-byte + 신규 3 키(`latest_work_mtime=expected_work_mtime`, `latest_verify_date_key="2026-04-20"`, `latest_verify_mtime=expected_verify_mtime`).
  - `:348` `self.assertEqual(dispatch_events[0]["source"], "supervisor")` byte-for-byte 유지.
- `tests/test_pipeline_runtime_supervisor.py:350-407` seq 543 monotonic
  - `:382-388` `date_keys` list comprehension byte-for-byte 유지.
  - `:390-392` 기존 3 어서션(`len(dispatch_events) == 2`, `date_keys == ["2026-04-18", "2026-04-20"]`, `date_keys == sorted(date_keys)`) byte-for-byte 유지.
  - `:393-398` 기존 additive loop의 `for event` + `payload =` + `date_key` consistency assert byte-for-byte 유지.
  - `:399-407` 신규 assertion set in-loop: `work_file = root / "work" / payload["latest_work"]` + `self.assertAlmostEqual(payload["latest_work_mtime"], work_file.stat().st_mtime, places=3)` + `self.assertEqual(payload["latest_verify"], "—")` (리그레션 락) + `self.assertEqual(payload["latest_verify_date_key"], "")` + `self.assertEqual(payload["latest_verify_mtime"], 0.0)`. loop 구조(`for event in dispatch_events:`) 변경 없음.
- `pipeline_runtime/control_writers.py`(seq 546 + 549), `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_control_writers.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py` 이번 라운드에서 수정되지 않음을 Read/Grep으로 확인.
- seq 408/.../521/527/530/533/536/539/543/546/549/552 shipped surface는 seq 533/seq 543 테스트 확장 두 지점을 제외하면 byte-for-byte 유지.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 5 tests in 0.034s`, `OK`. 5개 build_artifacts 테스트(`test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`, `test_build_artifacts_emits_dispatch_selection_event`, `test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify`, `test_build_artifacts_prefers_manifest_feedback_path_over_verify_body_scan`, `test_build_artifacts_uses_canonical_round_notes_only`) 전부 green. handoff 예상대로 seq 552 baseline 5건 유지.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 98 tests in 0.679s`, `OK`. seq 552 baseline 98과 정합. 새 red 없음.
- `python3 -m unittest tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 49 tests in 0.062s`, `OK` (7 + 6 + 36 = 49 정합). seq 549 / seq 546 / seq 527 + 530 contracts 유지.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check
  - `rg -n '"latest_work_mtime"|"latest_verify_date_key"|"latest_verify_mtime"' pipeline_runtime/supervisor.py` → 3 hits (`:876`, `:877`, `:878`). 신규 세 키가 emit payload literal 안에만 위치.
  - `rg -n 'verify_date_key' pipeline_runtime/supervisor.py` → 3 hits (`:867` 초기화, `:869` derivation, `:877` payload value). seq 552 `work_date_key`와 동일한 3-hit 패턴.
  - `rg -n '"dispatch_selection"' pipeline_runtime/supervisor.py` → 1 hit (`:871`, 단일 emit site).
  - `/work` grep 결과와 본 verify 측정 결과 모두 정합 (supervisor 9 mtime hits, tests 6 three-key hits, 1 assertAlmostEqual, 5 def test_build_artifacts, 98 def test_).
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`, `tests.test_pipeline_gui_backend`, `tests.test_smoke -k progress_summary|coverage`: `/work`에서 green 기록(143/46/11/27)을 남긴 범위 regression. 이번 편집은 supervisor emit-payload 3 keys + test 확장만으로 한정됐고 해당 모듈은 `_build_artifacts` emit payload 또는 해당 두 테스트를 호출/import하지 않으므로 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **AXIS-EMIT-PAYLOAD-ENRICH closed**: Gemini 554의 6-key shape가 payload source에서 한 번에 emit되는 형태로 완결됐습니다. downstream consumer는 이제 `date_key`, mtime pair, `latest_verify_date_key`를 재파싱하지 않고 바로 소비 가능.
- **AXIS-STALE-REFERENCE-AUDIT**: 여전히 오픈. `tests/test_pipeline_runtime_supervisor.py:1057` 근방 bare `"# verify\n"` fixture sweep 미수행.
- **AXIS-G7-AUTONOMY-PRODUCER**: seq 549 defensive gate를 load-bearing으로 만드는 producer-side wiring 미수행.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 다음 real dispatch 후 empirical monotonic + 6-key consistency 확인용 verify-lane instruction 미배포. 이번 라운드로 emit이 4개 파생 필드(`date_key`, `latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`)를 모두 싣기 때문에 다음 empirical trace 확인 축이 더 또렷해짐.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지 (이번 라운드는 production emit enrichment + unit test slice).
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-STALE-REFERENCE-AUDIT / AXIS-G7-AUTONOMY-PRODUCER / AXIS-DISPATCHER-TRACE-BACKFILL / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. AXIS-EMIT-PAYLOAD-ENRICH 축은 닫혔고, AXIS-DISPATCHER-TRACE-BACKFILL은 이제 더 또렷하지만 empirical trigger를 언제 잡을지 운영 타이밍이 개입됨. real operator-only blocker는 없음. 따라서 seq 556 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
