# 2026-04-20 g7 autonomy producer verification

## 변경 파일
- `verify/4/20/2026-04-20-g7-autonomy-producer-verification.md`

## 사용 skill
- `round-handoff`: seq 561 `.pipeline/claude_handoff.md`(AXIS-G7-AUTONOMY-PRODUCER: `classify_operator_candidate` mode-based `decision_class` default block 3-매핑 + `tests/test_pipeline_runtime_supervisor.py` direct unit test 1개 append) 구현 주장을 실제 HEAD에 대조하고, handoff가 요구한 narrowest 재검증 (`py_compile`, focused 신규 test, supervisor 99 + control_writers 7 + operator_request_schema 6 + schema 36 bundle, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 Gemini 560 권고대로 `pipeline_runtime/operator_autonomy.py:classify_operator_candidate`에 mode-based `decision_class` default 블록을 삽입하고, `tests/test_pipeline_runtime_supervisor.py`에 `classify_operator_candidate` direct unit test 1개를 append했다고 주장했습니다. AXIS-STALE-REFERENCE-AUDIT는 별도 docs 없이 `/work` audit trail로만 closed 선언. verify 라인은 (a) default block이 `visible_mode` / `routed_to` 결정 직후와 `fingerprint_source` 앞 정확한 위치에 삽입됐는지, (b) 3-매핑(`needs_operator`→`operator_only`, `triage`→`next_slice_selection`, `hibernate`→`internal_only`)이 정확한지, (c) Gemini 560이 지정하지 않은 `pending_operator` 등은 empty default 유지인지, (d) 새 test fixture의 reason_code 선택이 실제로 target `visible_mode`를 만드는지 (handoff는 `gemini_tiebreak` 등을 제안했지만 구현자는 다른 reason_code를 선택할 수 있음), (e) seq 527/530/533/536/539/543/546/549/552/555/521 contract가 byte-for-byte 유지됐는지, (f) 기존 adjacent 테스트 회귀가 없는지 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `pipeline_runtime/operator_autonomy.py:306-312` 신규 default block
  - `:306` `if not decision_class:` — seq 247 `decision_class = normalize_decision_class(meta.get("decision_class"))` 결과가 empty일 때만 분기.
  - `:307-308` `if visible_mode == "needs_operator": decision_class = "operator_only"`.
  - `:309-310` `elif visible_mode == "triage": decision_class = "next_slice_selection"`.
  - `:311-312` `elif visible_mode == "hibernate": decision_class = "internal_only"`.
  - 세 매핑 밖의 `visible_mode`(예: `pending_operator`, `normal`)는 `decision_class`가 empty 유지. Gemini 560이 지정하지 않은 스코프. seq 549 read-time gate의 empty pass-through 규약과 정확히 호환.
  - 블록 위치는 `:303-305`(`visible_mode` / `routed_to` 최종 결정)과 `:314-326`(`fingerprint_source`) 사이 — handoff가 요구한 대로 정확히 fingerprint와 return dict 양쪽에 default된 값이 동일하게 반영됨.
  - 함수 시그니처, 다른 분기(`:254-301`), return dict key 셋 모두 byte-for-byte 유지. import 추가 없음.
- `tests/test_pipeline_runtime_supervisor.py:13` 신규 import (단일 `from pipeline_runtime.operator_autonomy import (SUPPORTED_DECISION_CLASSES, classify_operator_candidate,)` 라인).
- `tests/test_pipeline_runtime_supervisor.py:4511-4540` 신규 메서드 `test_classify_operator_candidate_defaults_decision_class_per_visible_mode`
  - 3개 scenario를 `with self.subTest(mode=expected_mode):` 패턴으로 parametrize. 각 scenario는 `classify_operator_candidate("", control_meta={"reason_code": <value>}, now_ts=1_000.0)` 호출 후 `result["mode"] == expected_mode`, `result["decision_class"] in SUPPORTED_DECISION_CLASSES`, `result["decision_class"] == expected_decision_class` 세 assertion.
  - scenario 1: `reason_code="truth_sync_required"` → `mode="needs_operator"` → `decision_class="operator_only"`. `truth_sync_required`는 `_IMMEDIATE_REASON_CODES`이므로 `operator_policy="immediate_publish"`가 되고 `:271-273`에서 `mode="needs_operator"`로 강제되며 `operator_eligible=True`라 `visible_mode="needs_operator"` 유지. ✓
  - scenario 2: `reason_code="slice_ambiguity"` → `mode="triage"` → `decision_class="next_slice_selection"`. `slice_ambiguity`는 `_REASON_BEHAVIOR` 맵에서 `mode: "triage"`, `routed_to: "codex_followup"` 직접 매핑 (handoff가 예시한 `gemini_tiebreak` 대신 동등 경로). ✓
  - scenario 3: `reason_code="waiting_next_control"` → `mode="hibernate"` → `decision_class="internal_only"`. `waiting_next_control`은 `_REASON_BEHAVIOR`에서 `{"mode": "hibernate", "routed_to": "hibernate"}` 매핑. operator_policy가 internal_only여서 `operator_eligible=False` → `visible_mode=mode="hibernate"`. ✓
  - 세 scenario 모두 control_meta에 `decision_class`를 넣지 않아 새 default block이 실제로 load-bearing함을 증명.
  - 기존 98개 테스트 byte-for-byte 유지, 새 test 1개 추가로 총 99.
- `tests/test_pipeline_runtime_supervisor.py:4543-4544` `if __name__ == "__main__": unittest.main()` 블록이 새 test 바로 뒤에 위치 — handoff가 지정한 "class 끝 / module `if __name__` 블록 앞" 위치와 정합.
- AXIS-STALE-REFERENCE-AUDIT 별도 docs 파일 추가 없음. `/work` note의 `## 남은 리스크` 섹션에서 closed로만 기록. 오늘(2026-04-20) docs-only round count 0 유지.
- `pipeline_runtime/control_writers.py`(seq 546 + 549), `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `scripts/pipeline_runtime_gate.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_control_writers.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py` 이번 라운드에서 수정되지 않음을 Read/grep으로 확인.
- seq 408/.../521/527/530/533/536/539/543/546/549/552/555 shipped surface는 byte-for-byte 유지.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_defaults_decision_class_per_visible_mode`
  - 결과: `Ran 1 test in 0.001s`, `OK`. 3개 subTest 전부 통과. 타깃 단일 메서드 green 직접 확인.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_control_writers tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 148 tests in 0.755s`, `OK`. 99 + 7 + 6 + 36 = 148 정확 일치. seq 549 read-time gate가 새 default literal(`operator_only`, `next_slice_selection`, `internal_only`) 모두 canonical set 안이라 red 없이 통과함을 재확인 (control_writers 7 green).
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check (`/work` 기록과 직접 대조)
  - `rg -n 'def classify_operator_candidate' pipeline_runtime/operator_autonomy.py` → 1 hit (`:215`). `/work` 정합.
  - `rg -n 'decision_class = "(operator_only|next_slice_selection|internal_only)"' pipeline_runtime/operator_autonomy.py` → 3 hits (`:308`, `:310`, `:312`). `/work` 정합.
  - `rg -n 'if not decision_class:' pipeline_runtime/operator_autonomy.py` → 1 hit (`:306`). `/work` 정합.
  - `rg -n 'SUPPORTED_DECISION_CLASSES' pipeline_runtime/operator_autonomy.py` → 1 hit (`:53` definition). 다른 참조가 이 파일에는 없음을 확인.
  - `rg -n 'classify_operator_candidate|SUPPORTED_DECISION_CLASSES' tests/test_pipeline_runtime_supervisor.py` → 4 hits (`:13` import, `:4511` test def, `:4532` 호출, `:4539` 어서션). `/work` 정합.
  - `rg -n 'def test_classify_operator_candidate_defaults_decision_class_per_visible_mode' tests/test_pipeline_runtime_supervisor.py` → 1 hit (`:4511`).
  - `rg -n 'def test_' tests/test_pipeline_runtime_supervisor.py | wc -l` → 99 (baseline 98 +1).
- 실행하지 않은 항목 (명시):
  - `tests.test_watcher_core`(143) / `tests.test_pipeline_gui_backend`(46) / `tests.test_smoke -k progress_summary|coverage`(11/27): `/work`가 green으로 기록했고, watcher_core는 `classify_operator_candidate`를 import하긴 하지만(`watcher_core.py:63`) 이번 default block은 empty → canonical 전환만 추가했고 watcher-side consumer가 빈 문자열을 특별히 기대하지 않는 이상 회귀 없음. 본 verify round에서 재실행 생략.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **G7-AUTONOMY-PRODUCER 부분 closure**: `classify_operator_candidate` producer boundary에서 3개 매핑된 `visible_mode`(`needs_operator`, `triage`, `hibernate`)에서만 canonical default가 load-bearing. `pending_operator`, `normal` 등 다른 mode는 empty default 유지 — concrete use-case가 생기면 future slice에서 4번째 매핑 추가 가능. 현재 seq 549 gate는 empty pass-through라 red 없음.
- **AXIS-STALE-REFERENCE-AUDIT closed**: Gemini 560 기준 category-A(fix-needed) hit 0건으로 closure 선언. category-B 3건(`tests/test_pipeline_runtime_schema.py:403/432/478` bare `"# verify\n"` None-path 고정 fixture)은 의도적 고정. docs 파일은 추가하지 않았고 `/work` audit trail로만 closure 기록 — 오늘 docs-only round count 0 유지.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 여전히 오픈. live dispatcher emit이 이제 6-key shape(seq 555) + canonical decision_class(seq 561)까지 싣기 때문에 empirical confirmation 축이 더 또렷.
- **AXIS-EMIT-KEY-STABILITY-LOCK**: 여전히 오픈. seq 555 6-key shape을 test layer에서 잠그는 슬라이스 후보.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지.
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-DISPATCHER-TRACE-BACKFILL / AXIS-EMIT-KEY-STABILITY-LOCK / AXIS-G7-AUTONOMY-PRODUCER-EXTEND(pending_operator 등) / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. real operator-only blocker도 없음. 따라서 seq 562 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
