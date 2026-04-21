# 2026-04-20 operator_request DECISION_CLASS canonicalize verification

## 변경 파일
- `verify/4/20/2026-04-20-operator-request-decision-class-canonicalize-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 510 `.pipeline/claude_handoff.md`(G7-canonicalize, Gemini 509 advice — `SUPPORTED_DECISION_CLASSES` canonical frozenset 도입 + test import 전환 + 1개 메서드 rename) 구현 주장을 `pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py` 실제 상태와 대조했고, 5-test suite + `tests.test_pipeline_gui_backend` 45/OK/skipped=0 + smoke 4 subset(11/27/7/6) + canonical-set direct import sanity를 직접 재실행했습니다.

## 변경 이유
- seq 510 `.pipeline/claude_handoff.md`(Gemini 509 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-operator-request-decision-class-canonicalize.md`가 제출되었습니다.
- 목표는 `DECISION_CLASS` vocabulary를 `pipeline_runtime.operator_autonomy`로 승격해 `SUPPORTED_REASON_CODES` / `SUPPORTED_OPERATOR_POLICIES`와 동일한 canonical symbol 형태를 갖추고, `tests/test_operator_request_schema.py`가 inline observed set 대신 해당 canonical set을 import하도록 정리하는 것이었습니다. `advisory_only`는 Gemini 509의 explicit IN 결정을 그대로 반영.

## 핵심 변경
- `pipeline_runtime/operator_autonomy.py:53-62` — `SUPPORTED_DECISION_CLASSES: frozenset[str] = frozenset({...})`가 `SUPPORTED_REASON_CODES` 바로 뒤에 추가됐습니다. membership은 정확히 6개:
  - `operator_only`, `advisory_only`, `next_slice_selection`, `internal_only`, `truth_sync_scope`, `red_test_family_scope_decision`.
  - `advisory_only`는 Gemini 509의 forward-looking canonical IN decision. implement 시점 기준 `rg advisory_only`는 repo 전체에서 여전히 0 hit(추후 canonical adoption까지 dormant member).
  - annotation은 `frozenset[str]`, multi-line constructor shape로 `SUPPORTED_REASON_CODES` 스타일과 일관.
- `pipeline_runtime/operator_autonomy.py:174-175` — `normalize_decision_class`는 unchanged. 여전히 `normalize_reason_code` 위임 pass-through. runtime gating 미연결.
- `pipeline_runtime/operator_autonomy.py:247` — `classify_operator_candidate` 내부의 `decision_class = normalize_decision_class(meta.get("decision_class"))` 호출도 unchanged. `/work`가 해설했듯 `rg normalize_decision_class`가 2 hits(정의 + 호출)인 것은 정상이며, 함수 body가 건드려지지 않았음을 확인.
- `tests/test_operator_request_schema.py:4-8` — multi-line import 블록으로 `SUPPORTED_DECISION_CLASSES`, `SUPPORTED_OPERATOR_POLICIES`, `SUPPORTED_REASON_CODES` 동시 import. 종전 single-line import가 정렬된 multi-line으로 변형됨.
- `tests/test_operator_request_schema.py` inline `OBSERVED_DECISION_CLASSES` frozenset과 그 comment 완전 제거 확인. `rg OBSERVED_DECISION_CLASSES tests/` 0 hit.
- `tests/test_operator_request_schema.py:70-74` — `test_decision_class_is_observed` → `test_decision_class_is_canonical` rename + assertion set을 `SUPPORTED_DECISION_CLASSES`로 교체. 메서드 body는 handoff pin과 정확히 일치.
- `tests/test_operator_request_schema.py`의 다른 4개 test method(`test_canonical_header_parses_all_expected_fields` `:36`, `test_status_and_control_seq_in_first_12_lines` `:52`, `test_reason_code_is_canonical` `:61`, `test_operator_policy_is_canonical` `:64`), `FIXTURE_HEADER` `:10-21`, `_parse_operator_request_header` `:24-32`, trailing `if __name__ == "__main__"` 블록 모두 byte-for-byte 유지. test count 5 유지.
- `scripts/pipeline_runtime_gate.py`, `pipeline_runtime/control_writers.py`, 모든 `.pipeline/*.md`(stale operator_request.md 포함), `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 전부 미편집 확인.
- grep 결과 대조(직접 재실행):
  - `rg -n 'SUPPORTED_DECISION_CLASSES' pipeline_runtime/operator_autonomy.py` → 1 hit(`:53`). 기대치 일치.
  - `rg -n '"advisory_only"' pipeline_runtime/operator_autonomy.py` → 1 hit(`:56`). 기대치 일치.
  - `rg -n 'SUPPORTED_DECISION_CLASSES' tests/test_operator_request_schema.py` → 2 hits(`:5 import`, `:73 assertIn`). 기대치 일치.
  - `rg -n 'OBSERVED_DECISION_CLASSES' tests/test_operator_request_schema.py` → 0. 기대치 일치.
  - `rg -n 'OBSERVED_DECISION_CLASSES' tests/` → 0. stray 참조 없음.
  - `rg -n 'def test_decision_class_is_canonical' tests/test_operator_request_schema.py` → 1 hit(`:70`).
  - `rg -n 'def test_decision_class_is_observed' tests/test_operator_request_schema.py` → 0.
  - `rg -n 'def test_' tests/test_operator_request_schema.py` → 5 hits(`:36, :52, :61, :64, :70`).
  - `rg -n '@unittest.skip' tests/test_operator_request_schema.py` → 0.
  - `rg -n 'normalize_decision_class' pipeline_runtime/operator_autonomy.py` → 2 hits(`:174 정의`, `:247 호출`). handoff 기대치 1은 정의 기준이었고 `/work`가 정확히 해설; body 무변경 확인.
  - `rg -n '^SUPPORTED_' pipeline_runtime/operator_autonomy.py` → 3 hits(`:47`, `:48`, `:53`). 기대치 일치.
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py` → 1 hit(`:73`). seq 504 baseline 유지.
- canonical-set sanity rerun: `python3 -c "from pipeline_runtime.operator_autonomy import SUPPORTED_DECISION_CLASSES; assert len(SUPPORTED_DECISION_CLASSES) == 6; assert 'advisory_only' in SUPPORTED_DECISION_CLASSES; assert 'operator_only' in SUPPORTED_DECISION_CLASSES; print('OK')"` → `OK`.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `510` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 511.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `508` — seq 509 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `509` — seq 510 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded(drift literal 포함된 stale 상태 그대로).

## 검증
- 직접 코드 대조(경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 5 tests in 0.000s`, `OK`. renamed `test_decision_class_is_canonical` 포함 5개 전원 green.
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.068s`, `OK`. `OK (skipped=0)` 유지. seq 504 G12 baseline 회귀 없음.
- `python3 -c "from pipeline_runtime.operator_autonomy import SUPPORTED_DECISION_CLASSES; assert len(SUPPORTED_DECISION_CLASSES) == 6; assert 'advisory_only' in SUPPORTED_DECISION_CLASSES; assert 'operator_only' in SUPPORTED_DECISION_CLASSES; print('OK')"` → `OK`. `len == 6`, `advisory_only in`, `operator_only in` 직접 확인.
- `python3 -m unittest tests.test_smoke -k progress_summary` → `Ran 11 tests / OK`.
- `python3 -m unittest tests.test_smoke -k coverage` → `Ran 27 tests / OK`.
- `python3 -m unittest tests.test_smoke -k claims` → `Ran 7 tests / OK`.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 6 tests / OK`.
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py` → 출력 없음, 통과.
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_operator_request_schema.py` → 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 browser/웹 계약 변경 없음이라 의도적으로 생략.

## 남은 리스크
- **forward-looking `advisory_only` dormant canonical member**:
  - `SUPPORTED_DECISION_CLASSES`는 이제 6개 literal을 보장하지만, 그중 `advisory_only`는 implement 시점 기준 repo 전체 `rg` 0 hit입니다. Gemini 509의 명시적 IN 결정 기록이며, 이후 라운드가 실제로 `DECISION_CLASS: advisory_only`를 쓰기 시작하면 자동으로 canonical-통과가 됩니다. dormant 상태가 길어져서 설계 의도가 흐려지는 경우를 대비해 이 사실을 `/work`와 함께 기록해 두었습니다.
- **`normalize_decision_class` pass-through 유지**:
  - runtime 단에서 `DECISION_CLASS`를 canonical 집합으로 강제하지 않습니다. gate 또는 control-writer 쪽 wiring은 G7-gate-blocking 별도 슬라이스로 연기.
- **live `.pipeline/operator_request.md` drift 미처리**:
  - seq 462 파일이 여전히 non-canonical `REASON_CODE: advice_g5_not_bounded_first_sub_slice` literal을 들고 있습니다. advisory test가 실제 파일을 읽도록 넓히려면 drift-handling 전략(skip-if-stale / drift allowance / live truth-sync) 중 하나를 먼저 고정해야 하고, G7-live-file 슬라이스에서 다뤄야 합니다.
- **다음 슬라이스 ambiguity**:
  - 남은 후보: G7-live-file(advisory test를 실제 파일까지 확장, drift handling 필요), G7-gate-blocking(아직 premature), G3(incident 필요), G6-sub2/G6-sub3(환경/모호), G8-pin(exact slice 필요), G9/G10/G11(내부 cleanup).
  - 단독 dominant current-risk reduction이 뚜렷하지 않아 `.pipeline/gemini_request.md`로 arbitration을 여는 편이 `/verify` README 규칙과 일치. operator-only 결정 요소는 현재로선 없음.
- **seq 492 / seq 504 교훈 지속**: backend 계열 축을 다시 손댈 때는 11+ green supervisor_missing cells + quiescent-path cell 비교표가 여전히 필수. 이번 라운드는 해당 축 무변경이라 안전.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 target 2 files만 추가 수정.
