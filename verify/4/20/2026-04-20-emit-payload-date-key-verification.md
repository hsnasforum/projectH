# 2026-04-20 emit payload date_key verification

## 변경 파일
- `verify/4/20/2026-04-20-emit-payload-date-key-verification.md`

## 사용 skill
- `round-handoff`: seq 552 `.pipeline/claude_handoff.md` (AXIS-EMIT-PAYLOAD-ENRICH: `pipeline_runtime/supervisor.py:_build_artifacts` dispatch_selection emit payload에 `date_key` 한 키 additive 추가 + seq 533 sibling equality / seq 543 monotonic consistency 테스트 갱신) 구현 주장을 실제 HEAD에 대조하고, handoff가 요구한 narrowest 재검증 (`py_compile`, focused `-k build_artifacts`, 전체 supervisor 98, control_writers 7 / operator_request_schema 6 / schema 36, `git diff --check`, grep cross-check)을 직접 재실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 `dispatch_selection` emit payload에 `date_key` 키 하나만 additive로 추가하고, consumer 두 테스트(seq 533 sibling equality, seq 543 monotonic consistency)를 같은 슬라이스에서 갱신했다고 주장했습니다. verify 라인은 (a) emit site 변경이 target 2파일에만 한정됐는지, (b) return dict가 그대로인지, (c) em-dash/empty sentinel에서 `""`로 접히는 guard가 seq 543의 `!= "—"` 규약과 일치하는지, (d) seq 527/530/533/536/539/543/546/549/521 contract가 byte-for-byte 유지됐는지, (e) seq 543 monotonic 테스트의 additive loop가 기존 어서션을 건드리지 않았는지를 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `pipeline_runtime/supervisor.py:864-874` `_build_artifacts` emit block
  - `:864-866` 신규 local: `work_date_key = ""` + `if work_rel and work_rel != "—": work_date_key = Path(work_rel).name[:10]`. seq 543 monotonic 테스트 `:382`의 `!= "—"` 가드와 일치.
  - `:867-874` `self._append_event("dispatch_selection", {...})` 호출의 payload dict 리터럴이 2-key에서 3-key로 확장: `{"latest_work": work_rel, "latest_verify": verify_rel, "date_key": work_date_key}`. `latest_work` / `latest_verify` 순서/값 byte-for-byte 유지.
  - `:875-878` 반환 dict(`{"latest_work": {"path": work_rel, "mtime": work_mtime}, "latest_verify": {"path": verify_rel, "mtime": verify_mtime}}`) byte-for-byte 유지. emit payload만 커졌고 `_build_artifacts` 반환 계약은 불변.
  - 다른 emit site(`:1214`, `:1257`, `:1260`, `:1634`, `:1647`, `:1669`, `:1691`, `:1713`, `:1728`, `:1743`, `:1748`, `:1750`, `:1770`, `:2195`, `:2205`, `:2213`, `:2236`, `:2268`) 모두 byte-for-byte 유지. `_append_event`(`:287+`) signature/behavior 불변.
  - import 추가 없음. `from pathlib import Path`가 이미 존재해 새 derivation이 그대로 성립.
- `tests/test_pipeline_runtime_supervisor.py:335-342` seq 533 sibling equality block
  - `:337-341` 기존 2-key payload dict에 `"date_key": "2026-04-20"` 한 줄 추가. 다른 라인 byte-for-byte 유지. test 내 work_note 이름(`2026-04-20-observable-round.md`)에서 `[:10]`이 정확히 `"2026-04-20"`이 되므로 equality 통과.
- `tests/test_pipeline_runtime_supervisor.py:344-393` seq 543 monotonic test
  - `:385-387` 기존 3 어서션(`len(dispatch_events) == 2`, `date_keys == ["2026-04-18", "2026-04-20"]`, `date_keys == sorted(date_keys)`) byte-for-byte 유지.
  - `:388-393` 신규 additive loop: `for event in dispatch_events: payload = event["payload"]; self.assertEqual(payload["date_key"], Path(payload["latest_work"]).name[:10])`. emit key와 파싱 형식 consistency를 직접 잠금. 기존 `date_keys` list comprehension(`:377-383`)과 그 세 어서션은 건드리지 않았음을 Read로 확인.
- `pipeline_runtime/control_writers.py`(seq 546 + 549), `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_control_writers.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py` 이번 라운드에서 수정되지 않음을 Read/Grep으로 확인.
- seq 408/.../521/527/530/533/536/539/543/546/549 shipped surface는 seq 533/seq 543 두 테스트 보강 두 군데를 제외하면 byte-for-byte 유지.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts`
  - 결과: `Ran 5 tests in 0.033s`, `OK`. `test_build_artifacts_returns_round_markdown_entries`는 class 내 다른 method name prefix여서 `-k build_artifacts`에 잡힘/미잡힘은 구현별로 다르지만, 이번 run은 5건 전부 green. `/work` 기록 5와 정합 (handoff snapshot 예상 4는 dirty-worktree pre-existing 추가 테스트가 포함돼 5로 관측된 것을 `/work`가 투명하게 기록).
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 98 tests in 0.691s`, `OK`. seq 546 closeout baseline 98과 정합. 새 red 없음.
- `python3 -m unittest tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 49 tests in 0.054s`, `OK` (7 + 6 + 36 = 49 정합). seq 549 / seq 546 / seq 527 + 530 contracts 전부 유지.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check (`/work`와 정합)
  - `rg -n '"dispatch_selection"' pipeline_runtime/supervisor.py` → 1 hit (`:868`). `/work` 기록 정합.
  - `rg -n '"date_key"' pipeline_runtime/supervisor.py` → 1 hit (`:872`). 신규 payload key.
  - `rg -n 'work_date_key' pipeline_runtime/supervisor.py` → 3 hits (`:864`, `:866`, `:872`). `/work`가 이유와 함께 정직하게 기록(handoff 예상 2와 실측 3의 차이는 sentinel-guard 두 줄이 한 이름을 2번 언급하는 구조 때문).
  - `rg -n '"date_key"' tests/test_pipeline_runtime_supervisor.py` → 2 hits (`:340` seq 533 sibling equality, `:391` seq 543 additive loop).
  - `rg -n 'Path\(.*\)\.name\[:10\]' tests/test_pipeline_runtime_supervisor.py` → 2 hits (`:378` seq 543 기존 list comprehension, `:392` seq 543 additive loop). `/work` 기록 정합.
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`, `tests.test_pipeline_gui_backend`, `tests.test_smoke -k progress_summary|coverage`: `/work`에서 green 기록(143/46/11/27)을 남긴 범위 regression. 이번 편집은 supervisor emit-payload 1 key + test 2 어서션 변경으로 한정됐고 해당 모듈은 `_build_artifacts` emit payload 혹은 해당 두 테스트를 호출/import하지 않으므로 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **AXIS-EMIT-PAYLOAD-ENRICH 부분 closure**: `date_key` 한 키는 이제 payload source에서 한 번만 계산되어 emit됨. 남은 optional keys(`latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`)는 필요 시 future round 후보.
- **seq 542 typo family**: `date_key`를 payload source에 넣음으로써 downstream consumer가 다시 파싱할 필요가 줄었고 emit-vs-parse consistency가 seq 543 monotonic test에서 직접 잠기지만, 이미 존재하는 파싱 기반 consumer가 있다면 이 컨트랙트 전환은 점진적으로 진행돼야 함.
- **AXIS-STALE-REFERENCE-AUDIT**: 여전히 오픈. `tests/test_pipeline_runtime_supervisor.py:1057` 근방 bare `"# verify\n"` fixture sweep 미수행.
- **AXIS-G7-AUTONOMY-PRODUCER**: seq 549 defensive gate를 load-bearing으로 만드는 producer-side wiring은 미수행.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 다음 real dispatch 후 empirical monotonic 확인용 verify-lane instruction 미배포.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지 (이번 라운드는 production emit enrichment + unit test slice).
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-EMIT-PAYLOAD-ENRICH 잔여 3 keys / AXIS-STALE-REFERENCE-AUDIT / AXIS-G7-AUTONOMY-PRODUCER / AXIS-DISPATCHER-TRACE-BACKFILL / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. real operator-only blocker도 없음. 따라서 seq 553 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
