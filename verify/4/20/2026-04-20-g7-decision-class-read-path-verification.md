# 2026-04-20 g7 decision_class read-path verification

## 변경 파일
- `verify/4/20/2026-04-20-g7-decision-class-read-path-verification.md`

## 사용 skill
- `round-handoff`: seq 549 `.pipeline/claude_handoff.md` (AXIS-G7-DECISION-CLASS-READ-PATH: `validate_operator_candidate_status`에 세 번째 frozenset `SUPPORTED_DECISION_CLASSES` read-time enforcement + `tests/test_pipeline_runtime_control_writers.py` 회귀 1건 append) 구현 주장을 실제 HEAD 상태에 대조하고, handoff가 요구한 narrowest 재검증 (`py_compile`, 전체 control_writers 7, focused 3-메서드 개별, `tests.test_operator_request_schema` 6, `tests.test_pipeline_runtime_schema` 36, `git diff --check`, grep cross-check)을 직접 재실행했습니다.

## 변경 이유
- 새 `/work` 라운드가 control-writers owner boundary read path에 세 번째 canonical 프레임셋 `SUPPORTED_DECISION_CLASSES`(6-member)를 대칭 추가하고, `decision_class` field를 `autonomy` dict에서 읽되 empty pass-through를 유지한다고 주장했습니다. verify 라인은 (a) 이번 라운드 편집이 target 2파일에만 한정됐는지, (b) 새 membership 검사가 seq 546 `reason_code`/`operator_policy` 블록 바로 뒤에 대칭으로 들어갔는지, (c) 기존 empty-passthrough 불변(seq 546 sibling 두 번째 호출 + 신규 라운드 사이드 효과 없음)이 유지됐는지, (d) seq 527/530/533/536/539/543/546/521 contract가 byte-for-byte 보존됐는지, (e) `tests/test_operator_request_schema.py`가 여전히 6 green인지를 확인해야 했습니다.

## 핵심 변경 (verify 관점에서 본 HEAD 스냅샷)
- `pipeline_runtime/control_writers.py:6-13` import 블록
  - 기존 `from .operator_autonomy import (...)`에 `SUPPORTED_DECISION_CLASSES`(`:7`)만 alphabetical prefix로 추가. 별도 `import` statement 도입 없음. `from .schema import atomic_write_text`(`:14`) byte-for-byte.
- `pipeline_runtime/control_writers.py:229-268` `validate_operator_candidate_status`
  - `:238` 신규 local `decision_class = str(autonomy.get("decision_class") or "").strip()`. 기존 `:232-237` 필드 추출(`control`, `autonomy`, `active_control_file`, `active_control_status`, `autonomy_mode`, `reason_code`, `operator_policy`, `classification_source`) 유지.
  - `:240-246` `is_operator_candidate` 판정 로직 byte-for-byte 유지 (decision_class는 의도적으로 is_operator_candidate 신호에 포함하지 않음 — 기존 gate 확장 없음).
  - `:247-248` early-return, `:249-253` `classification_source` raise(seq 546), `:254-256` seq 546 `reason_code` block, `:257-262` seq 546 `operator_policy` block 모두 byte-for-byte 유지.
  - `:263-268` 신규 block: `normalized_decision_class = normalize_decision_class(decision_class)` + `if normalized_decision_class and normalized_decision_class not in SUPPORTED_DECISION_CLASSES: raise ValueError(f"unsupported decision_class: {decision_class}")`. empty/unknown 토큰은 `normalize_decision_class`(→ `normalize_reason_code`)이 `""`로 접으므로 현행 caller(decision_class 미포함 autonomy dict)는 계속 통과.
  - 함수 시그니처, imports(`:6-13`), `validate_operator_request_headers`(`:32-60`: presence-only decision_class 검사 `:58-60` 유지), `render_implement_blocked`, `render_operator_request` 경로는 byte-for-byte 유지.
- `tests/test_pipeline_runtime_control_writers.py:142-160` 신규 메서드 `test_validate_operator_candidate_status_rejects_unsupported_decision_class_literal`
  - negative-only shape: `reason_code="slice_ambiguity"` + `operator_policy="gate_24h"` + `classification_source="reason_code"` + `decision_class="not_a_real_decision_class_literal"` → `assertRaisesRegex(ValueError, "unsupported decision_class")` 통과 확인.
  - seq 546 `:107-140` sibling 바로 뒤 + `test_no_non_test_direct_writes_for_operator_or_implement_blocked`(`:162`) 바로 앞에 삽입됨을 Read로 확인.
  - 기존 6개 테스트 byte-for-byte 유지. positive empty-passthrough는 seq 546 sibling `test_validate_operator_candidate_status_requires_structured_classification_source`(`:78-106`)의 두 번째 호출이 계속 담당.
- `tests/test_operator_request_schema.py` 건드리지 않음 (Gemini 545 placement 교정 존중). `Ran 6 / OK` 유지.
- `scripts/pipeline_runtime_gate.py`, `pipeline_runtime/operator_autonomy.py`, `pipeline_runtime/schema.py`, `pipeline_runtime/supervisor.py`, `watcher_core.py`, `verify_fsm.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md` 이번 라운드에서 수정되지 않음을 grep + Read로 확인.
- seq 408/.../521/527/530/533/536/539/543/546 shipped surface byte-for-byte 유지.

## 검증
- `python3 -m py_compile pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음, exit 0 (`OK_PYCOMPILE`).
- `python3 -m unittest -v tests.test_pipeline_runtime_control_writers`
  - 결과: `Ran 7 tests in 0.005s`, `OK`. 7개 test 개별 모두 `ok` 라벨 확인 (신규 `test_validate_operator_candidate_status_rejects_unsupported_decision_class_literal` 포함).
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_runtime_schema`
  - 결과: `Ran 42 tests in 0.048s`, `OK`. 6 + 36 합계가 정확히 일치. Gemini 545 placement 교정 존중 (7로 늘지 않음), `pipeline_runtime/schema.py:22-25` pre-existing dirty label-rename 그대로.
- `git diff --check -- pipeline_runtime/control_writers.py tests/test_pipeline_runtime_control_writers.py`
  - 결과: 출력 없음 (`OK_DIFF`).
- grep cross-check (`/work`와 정합)
  - `rg -n 'def validate_operator_candidate_status' pipeline_runtime/control_writers.py` → 1 hit (`:229` — handoff snapshot `:228`에서 import 1줄 추가로 +1 shift 됐음을 `/work`에서 투명하게 기록).
  - `rg -n 'unsupported reason_code|unsupported operator_policy|unsupported decision_class' pipeline_runtime/control_writers.py` → 5 hits (`:53`, `:57`, `:256`, `:262`, `:268`). 신규 `:268` = `validate_operator_candidate_status` read-path의 3번째 frozenset raise.
  - `rg -n 'SUPPORTED_REASON_CODES|SUPPORTED_OPERATOR_POLICIES|SUPPORTED_DECISION_CLASSES' pipeline_runtime/control_writers.py` → 9 hits (`:7`, `:8`, `:9`, `:52`, `:56`, `:173`, `:255`, `:260`, `:266`). pre-edit 7 + 신규 import 1(`:7`) + 신규 membership check 1(`:266`).
  - `rg -n 'normalize_decision_class' pipeline_runtime/control_writers.py` → 3 hits (`:10` import + `:59` write-time `validate_operator_request_headers` + `:263` 신규 read-time).
  - `rg -n 'def test_validate_operator_candidate_status' tests/test_pipeline_runtime_control_writers.py` → 3 hits (`:78`, `:107`, `:142`). seq 546 두 + seq 549 하나.
  - `rg -n 'def test_' tests/test_pipeline_runtime_control_writers.py` → 7 (`/work` count 정합).
  - `rg -n 'def test_' tests/test_operator_request_schema.py` → 6 (불변).
  - `SUPPORTED_DECISION_CLASSES` frozenset 길이 = 6 (`python3 -c` 확인과 `/work` 기록 일치).
- 실행하지 않은 항목 (명시):
  - `tests.test_pipeline_runtime_supervisor`, `tests.test_watcher_core`, `tests.test_pipeline_gui_backend`, `tests.test_smoke -k progress_summary|coverage`: `/work`에서 green 기록(98/143/46/11/27)을 남긴 범위 regression. 이번 라운드 편집은 `control_writers.py` + 해당 테스트 파일로만 국한됐고 supervisor/watcher_core/pipeline_gui_backend/smoke는 `validate_operator_candidate_status`의 decision_class 경로를 호출하지 않으므로 본 verify round에서 재실행 생략. seq 546 verify round에서 supervisor 98 + schema 36 정합을 이미 확인했고, 오늘 본 verify round도 schema 36 정합을 재확인.
  - `tests.test_web_app`, Playwright, `make e2e-test`: browser-visible 계약 변경 없음. 의도적 생략.
  - full-repo dirty worktree audit: 범위 밖.

## 남은 리스크
- **G7 gate fully closed at control-writers owner boundary**: read-time 3-frozenset enforcement(`SUPPORTED_REASON_CODES`, `SUPPORTED_OPERATOR_POLICIES`, `SUPPORTED_DECISION_CLASSES`) 완결 + write-time `validate_operator_request_headers`(`:32-60`) 유지. 현재 caller가 `autonomy["decision_class"]`를 carry하지 않기에 production behavior 변경은 없고, future producer wiring에 대한 defensive gate 성격.
- **decision_class는 `autonomy` dict에서 여전히 optional**: 이번 라운드는 producer-side wiring을 건드리지 않았음. 만약 추후 `autonomy["decision_class"]`가 필수화되면 is_operator_candidate 신호 확장 여부와 함께 재검토 필요.
- **AXIS-STALE-REFERENCE-AUDIT**: 여전히 오픈. `tests/test_pipeline_runtime_supervisor.py:1057` 근방 bare `"# verify\n"` fixture sweep 미수행.
- **AXIS-EMIT-PAYLOAD-ENRICH**: 여전히 오픈. seq 542 typo 클래스를 payload source에서 닫는 슬라이스 후보.
- **AXIS-DISPATCHER-TRACE-BACKFILL**: 다음 real dispatch 후 empirical monotonic 확인용 verify-lane instruction 미배포.
- **G4, G11, G8-pin, G3, G9, G10, G6-sub2, G6-sub3**: 계속 deferred.
- **`tests.test_web_app`** 10건 `LocalOnlyHTTPServer` PermissionError baseline 유지.
- **Docs-only round count**: 오늘(2026-04-20) 0 유지 (이번 라운드는 production validation + unit test slice).
- **Dirty worktree**: broad unrelated dirty 파일 + `pipeline_runtime/schema.py:22-25` pre-existing label-rename diff 그대로. 이번 verify가 추가 stage하거나 reset하지 않음.
- **next slice ambiguity → Gemini-first**: 남은 후보(AXIS-STALE-REFERENCE-AUDIT / AXIS-EMIT-PAYLOAD-ENRICH / AXIS-DISPATCHER-TRACE-BACKFILL / G4 / G5-DEGRADED-BASELINE docs / G6-TEST-WEB-APP / G11 / G8-PIN)는 축이 서로 다르고 dominant current-risk reduction이 명확하지 않음. G7-family는 이번 라운드로 saturated. real operator-only blocker도 없음. 따라서 seq 550 next-control은 `.pipeline/operator_request.md` 대신 `.pipeline/gemini_request.md`로 여는 것이 맞습니다.
