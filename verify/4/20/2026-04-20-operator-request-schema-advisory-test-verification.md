# 2026-04-20 operator_request schema advisory test verification

## 변경 파일
- `verify/4/20/2026-04-20-operator-request-schema-advisory-test-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 507 `.pipeline/claude_handoff.md`(G7 advisory-mode operator-request schema test, Gemini 506 advice + handoff-side `DECISION_CLASS` vocabulary 교정) 구현 주장을 `tests/test_operator_request_schema.py` 실제 상태와 대조했고, 새 5-test suite + `tests.test_pipeline_gui_backend` 45/OK/skipped=0 + smoke 4 subset(11/27/7/6)을 직접 재실행했습니다.

## 변경 이유
- seq 507 `.pipeline/claude_handoff.md`(Gemini 506 advice + DECISION_CLASS 어휘 교정)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-operator-request-schema-advisory-test.md`가 제출되었습니다.
- 목표는 advisory-mode로 `operator_request.md` 상단 12줄 header의 `REASON_CODE` / `OPERATOR_POLICY` / `DECISION_CLASS`가 각자의 canonical(또는 observed) 집합에 속하는지 검증하는 self-contained unit test를 추가하고, production `.pipeline/operator_request.md` / `pipeline_runtime/operator_autonomy.py` / gate 코드는 일체 건드리지 않는 것이었습니다.

## 핵심 변경
- `tests/test_operator_request_schema.py` 새 파일 1개만 추가(86줄, 핸드오프 "under ~100 lines" 가드 안).
- `:4` — `pipeline_runtime.operator_autonomy`에서 `SUPPORTED_OPERATOR_POLICIES`, `SUPPORTED_REASON_CODES` 직접 import. 어휘 리터럴을 test 안에 중복 선언하지 않음.
- `:7-15` — `OBSERVED_DECISION_CLASSES = frozenset({"operator_only", "next_slice_selection", "internal_only", "truth_sync_scope", "red_test_family_scope_decision"})`. 상단에 `rg DECISION_CLASS:` scan을 source로 다시 확인하라는 한 줄 comment. Gemini advice 506의 `advisory_only`는 의도적으로 제외.
- `:17-28` — `FIXTURE_HEADER` raw-string, 핸드오프가 고정한 내용 그대로(STATUS/CONTROL_SEQ/REASON_CODE=slice_ambiguity/OPERATOR_POLICY=gate_24h/DECISION_CLASS=operator_only + DECISION_REQUIRED/BASED_ON_WORK/BASED_ON_VERIFY + blank line + Reason: body line).
- `:31-39` — `_parse_operator_request_header(text) -> dict[str, str]` inline helper, 첫 blank line 전까지 `^([A-Z_]+):\s*(.*)$` 정규식으로 header key/value 수집.
- `:42-81` — `OperatorRequestHeaderSchemaTests`의 5개 test method(`test_canonical_header_parses_all_expected_fields`, `test_status_and_control_seq_in_first_12_lines`, `test_reason_code_is_canonical`, `test_operator_policy_is_canonical`, `test_decision_class_is_observed`). 각 메서드는 핸드오프가 기술한 어설션 모양과 정확히 일치.
- `:84-85` — 표준 `if __name__ == "__main__": unittest.main()` 블록.
- `pipeline_runtime/operator_autonomy.py` / `pipeline_runtime/control_writers.py` / `scripts/pipeline_runtime_gate.py` / 모든 `.pipeline/*.md` / `pipeline_gui/backend.py` / `tests/test_pipeline_gui_backend.py` 는 의도적으로 미편집(git status 기준 tests/test_operator_request_schema.py 단독 추가).
- grep 결과 대조(직접 재실행):
  - `rg -n '^from pipeline_runtime.operator_autonomy' tests/test_operator_request_schema.py` → 1 hit(`:4`). 핸드오프 기대치 일치.
  - `rg -n 'SUPPORTED_REASON_CODES' tests/test_operator_request_schema.py` → 2 hits(`:4 import`, `:69 assertIn`). 기대치 일치.
  - `rg -n 'SUPPORTED_OPERATOR_POLICIES' tests/test_operator_request_schema.py` → 2 hits(`:4 import`, `:74 assertIn`). 기대치 일치.
  - `rg -n 'OBSERVED_DECISION_CLASSES' tests/test_operator_request_schema.py` → 2 hits(`:7 정의`, `:80 assertIn`). 기대치 일치.
  - `rg -n '@unittest.skip' tests/test_operator_request_schema.py` → 0. 기대치 일치.
  - `rg -n 'def test_' tests/test_operator_request_schema.py` → 5 hits(`:43, :59, :68, :71, :77`). 기대치 일치.
  - `rg -n 'advisory_only' tests/test_operator_request_schema.py` → 0. Gemini 리터럴 교정 성공 확인.
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py` → 1 hit(`:73`). seq 504 G12 baseline 유지.
- 추가 truth-scan 재실행:
  - `rg -n 'advisory_only' tests pipeline_runtime .pipeline/README.md .pipeline/operator_request.md` → 0. `/work` 주장 재확인.
  - `rg -n 'DECISION_CLASS: advisory_only' .pipeline tests pipeline_runtime` → 0. `/work` 주장 재확인.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `507` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 508.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `505` — seq 506 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `506` — seq 507 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드 대조(경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 5 tests in 0.000s`, `OK`. 5개 어설션이 전부 통과.
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.076s`, `OK`. `OK (skipped=0)` 유지. seq 504 G12 baseline 회귀 없음.
- `python3 -m unittest tests.test_smoke -k progress_summary` → `Ran 11 tests / OK`.
- `python3 -m unittest tests.test_smoke -k coverage` → `Ran 27 tests / OK`.
- `python3 -m unittest tests.test_smoke -k claims` → `Ran 7 tests / OK`.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 6 tests / OK`.
- `python3 -m py_compile tests/test_operator_request_schema.py` → 출력 없음, 통과.
- `git diff --check -- tests/test_operator_request_schema.py` → 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 browser/웹 계약 변경 없음이라 의도적으로 생략.

## 남은 리스크
- **advisory-mode only**:
  - 이 test는 self-contained `FIXTURE_HEADER`만 검증하고 실제 `.pipeline/operator_request.md` 파일은 열지 않습니다. 따라서 live file의 drift는 잡히지 않습니다. live file parse까지 넓히는 것은 별도 slice 후보.
- **DECISION_CLASS 어휘 divergence**:
  - Gemini advice 506은 `{operator_only, advisory_only, red_test_family_scope_decision}`를 제안했지만 이번 handoff/implementation은 observed set `{operator_only, next_slice_selection, internal_only, truth_sync_scope, red_test_family_scope_decision}`를 채택했습니다. 둘 중 어느 쪽이 authoritative set인지(또는 양쪽의 교집합/합집합으로 canonicalize할지)는 다음 라운드의 의사결정 여지로 남아 있습니다. 이는 어휘 계약 설계 영역이라 Gemini arbitration 또는 operator 결정 대상.
- **`SUPPORTED_DECISION_CLASSES` frozenset 미도입**:
  - `pipeline_runtime/operator_autonomy.py`에 canonical set이 없고, `normalize_decision_class`가 pass-through이라 runtime 단에서 vocabulary가 강제되지 않습니다. test 안의 `OBSERVED_DECISION_CLASSES`는 수동 유지이며, 새 DECISION_CLASS literal이 도입되면 의도적 fail이 드러나도록 설계된 drift-detection 테스트입니다.
- **gate integration 미연결**:
  - `scripts/pipeline_runtime_gate.py`에 blocking check이 연결되지 않았습니다. advisory-mode 유지. blocking 전환은 별도 slice 후보.
- **다음 슬라이스 ambiguity**:
  - 남은 후보: G3(reinvestigation tuning, 증거 필요), G6-sub2/G6-sub3(환경/모호), G8-pin(memory-foundation, exact pin 필요), G9/G10/G11(내부 cleanup), 그리고 새로 부상한 G7 follow-ups(a: live-file parse로 확장 / b: `advisory_only` 채택 여부 + `SUPPORTED_DECISION_CLASSES` canonicalize / c: gate blocking 전환).
  - dominant current-risk reduction이 뚜렷하지 않고 여러 축이 overlap되어 `.pipeline/gemini_request.md`로 arbitration을 여는 편이 `/verify` README 규칙과 일치합니다. operator-only 결정으로 볼 만한 요소(어휘 canonicalize)는 있지만, 먼저 Gemini tie-break를 거친 뒤 남는 핵심 결정만 operator에 올리는 게 순서상 맞습니다.
- **seq 492 / seq 504 교훈 지속**: backend 축에 다시 손댈 때는 11+ green supervisor_missing cells + 1 quiescent-path cell 전체와 먼저 비교표를 그립니다. 이번 슬라이스는 backend 무변경이라 해당 축은 안전.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 `tests/test_operator_request_schema.py` 단일 신규 파일만 추가.
