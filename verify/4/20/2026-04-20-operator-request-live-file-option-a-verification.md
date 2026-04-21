# 2026-04-20 operator_request live-file option A verification

## 변경 파일
- `verify/4/20/2026-04-20-operator-request-live-file-option-a-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 513 `.pipeline/claude_handoff.md`(G7-live-file option A, Gemini 512 advice — advisory test를 live file까지 확장하되 REASON_CODE drift에 skipTest) 구현 주장을 `tests/test_operator_request_schema.py` 실제 상태와 대조했고, 6-test suite + `-v` 단독 rerun(skip 메시지 확인) + `tests.test_pipeline_gui_backend` 45/OK/skipped=0 + smoke 4 subset(11/27/7/6)을 직접 재실행했습니다.

## 변경 이유
- seq 513 `.pipeline/claude_handoff.md`(Gemini 512 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-operator-request-live-file-option-a.md`가 제출되었습니다.
- 목표는 실제 `.pipeline/operator_request.md`의 drift를 advisory-mode로 감지하되, 현재 stale `REASON_CODE=advice_g5_not_bounded_first_sub_slice`에 걸려 red가 되지 않도록 file-absent + REASON_CODE-drift 두 경로에서 `self.skipTest`로 빠지는 6번째 test method를 추가하는 것이었습니다. live control slot은 truth-sync하지 않음.

## 핵심 변경
- `tests/test_operator_request_schema.py:2` — `from pathlib import Path`가 stdlib import block의 `import re`와 `import unittest` 사이에 추가됐습니다. alphabetical order는 아니지만 stdlib block 안에 위치한다는 점은 유지됐고, 기존 project import block(`:5-9`)은 그대로입니다.
- `tests/test_operator_request_schema.py:77-86` — 새 `test_live_operator_request_header_canonical` 추가. post-edit shape은 handoff 513 pin과 정확히 일치:
  - `:78` `live_file = Path(__file__).parent.parent / ".pipeline" / "operator_request.md"` — path resolution 확인.
  - `:79-80` file-absent → `self.skipTest("operator_request.md not present")`.
  - `:81` `header = _parse_operator_request_header(live_file.read_text(encoding="utf-8"))` — 기존 파서 재사용. `read_text(encoding="utf-8")` 명시.
  - `:82-84` `reason_code not in SUPPORTED_REASON_CODES` → `self.skipTest(f"Live file drift detected: REASON_CODE={reason_code!r}")`. `!r` 포맷.
  - `:85-86` `self.assertIn(header.get("OPERATOR_POLICY", ""), SUPPORTED_OPERATOR_POLICIES)` + `self.assertIn(header.get("DECISION_CLASS", ""), SUPPORTED_DECISION_CLASSES)`.
- 기존 5개 test method(`test_canonical_header_parses_all_expected_fields`, `test_status_and_control_seq_in_first_12_lines`, `test_reason_code_is_canonical`, `test_operator_policy_is_canonical`, `test_decision_class_is_canonical`), `FIXTURE_HEADER` `:11-22`, `_parse_operator_request_header` `:25-33` 전부 byte-for-byte unchanged 확인.
- `pipeline_runtime/operator_autonomy.py`, `scripts/pipeline_runtime_gate.py`, `pipeline_runtime/control_writers.py`, `.pipeline/operator_request.md`(stale 상태 그대로), `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 전부 미편집. git diff로 간접 확인.
- grep 결과 대조(직접 재실행):
  - `rg -n '^from pathlib import Path' tests/test_operator_request_schema.py` → 1 hit(`:2`).
  - `rg -n 'def test_live_operator_request_header_canonical' tests/test_operator_request_schema.py` → 1 hit(`:77`).
  - `rg -n 'def test_' tests/test_operator_request_schema.py` → 6 hits(`:37, :53, :62, :65, :71, :77`).
  - `rg -n 'self.skipTest' tests/test_operator_request_schema.py` → 2 hits(`:80 file-absent`, `:84 drift`).
  - `rg -n 'Live file drift detected: REASON_CODE=' tests/test_operator_request_schema.py` → 1 hit(`:84`).
  - `rg -n '@unittest.skip' tests/test_operator_request_schema.py` → 0.
  - `rg -n 'FIXTURE_HEADER' tests/test_operator_request_schema.py` → 6 hits(정의 + 5 references). 새 테스트가 참조 안 함 확인.
  - `rg -n '_parse_operator_request_header\(' tests/test_operator_request_schema.py` → 6 hits(handoff 기대치 5는 definition 제외 counting이었고, rg가 함께 잡는 게 정상. `/work`가 정확히 해설: 1 definition + 5 references including new test).
  - `rg -n 'live_file' tests/test_operator_request_schema.py` → 3 hits(`:78 path 할당`, `:79 .exists()`, `:81 .read_text()`). 기대치 일치.
  - `rg -n 'SUPPORTED_DECISION_CLASSES' pipeline_runtime/operator_autonomy.py` → 1 hit(`:53 seq 510 baseline 유지`).
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py` → 1 hit(`:73 seq 504 baseline 유지`).
- path sanity 재확인: `python3 -c "from pathlib import Path; p = Path('tests/test_operator_request_schema.py').resolve().parent.parent / '.pipeline' / 'operator_request.md'; print(p, p.exists())"` → `/home/xpdlqj/code/projectH/.pipeline/operator_request.md True`. file-absent branch가 조용히 skip할 위험 없음 확인.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `513` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 514.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `511` — seq 512 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `512` — seq 513 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded(이번 슬라이스가 drift signal을 보내는 대상).

## 검증
- 직접 코드 대조(경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_operator_request_schema`
  - 결과: `Ran 6 tests in 0.001s`, `OK (skipped=1)`. baseline transition `OK(5) → OK (skipped=1, ran=6)`.
- `python3 -m unittest tests.test_operator_request_schema.OperatorRequestHeaderSchemaTests.test_live_operator_request_header_canonical -v`
  - 결과: `skipped "Live file drift detected: REASON_CODE='advice_g5_not_bounded_first_sub_slice'"`. skip 분기 drift 경로가 실제로 탔고, file-absent 경로가 잘못 탄 게 아님을 재확인.
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.054s`, `OK`. `OK (skipped=0)` 유지. seq 504 G12 baseline 회귀 없음.
- `python3 -m unittest tests.test_smoke -k progress_summary` → `Ran 11 tests / OK`.
- `python3 -m unittest tests.test_smoke -k coverage` → `Ran 27 tests / OK`.
- `python3 -m unittest tests.test_smoke -k claims` → `Ran 7 tests / OK`.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 6 tests / OK`.
- `python3 -m py_compile tests/test_operator_request_schema.py` → 출력 없음, 통과.
- `git diff --check -- tests/test_operator_request_schema.py` → 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 browser/웹 계약 변경 없음이라 의도적으로 생략.

## 남은 리스크
- **드리프트 감지 행동 확인**:
  - 현재 repo state에서 live 테스트는 의도적으로 skip되며, skip 메시지가 stale literal `'advice_g5_not_bounded_first_sub_slice'`를 포함해 audit trail이 남습니다. 이후 라운드가 `.pipeline/operator_request.md`를 canonical `REASON_CODE`로 truth-sync하면 추가 test edit 없이 전체 assert가 실행됩니다.
  - live 파일의 `OPERATOR_POLICY=gate_24h` / `DECISION_CLASS=red_test_family_scope_decision`은 둘 다 canonical set에 포함되어 있어, 지금은 skip으로 빠지지만 `:85-86`의 assertIn이 이미 wired된 상태라 truth-sync 직후 drift가 발생하면 바로 잡힙니다.
- **deferred G7 분기 유지**:
  - option B(allowlist)는 현재 1개 stale literal에 대한 maintenance cost가 드문 drift signal만 잡아 option A보다 비용 대비 이득이 낮은 상태.
  - option C(truth-sync live file)는 Gemini 511 guardrail대로 operator routing이 필요한 영역.
  - gate blocking 전환은 option A가 실제 drift 신호를 한 라운드 이상 제공한 뒤에 검토하는 게 자연스럽습니다.
- **runtime gating 미연결**:
  - `normalize_decision_class` / `normalize_reason_code` 여전히 pass-through. 세 literal의 gate/control-writer 단 enforcement는 별도 슬라이스.
- **다음 슬라이스 ambiguity + G7 family saturation 조짐**:
  - 남은 후보: G7-live-file option B/C(문턱 결정 필요), G7-gate-blocking(premature), G3(incident 필요), G8-pin(tight pin 필요), G11(concrete audit 필요), G9/G10(내부 cleanup), G6-sub2/sub3(환경/모호).
  - G7 family는 seq 507/510/513으로 오늘 3라운드 연속 landed. 같은 family는 아직 production test/code 중심이라 docs-only 3+ rule에 해당하지 않지만, 다음 라운드는 다른 G-axis로 pivot하는 게 추가 leverage 확보 측면에서 자연스러울 수 있습니다. `.pipeline/gemini_request.md`로 arbitration을 여는 편이 `/verify` README 규칙과 일치. operator-only 결정은 현재 없음(stale control slot truth-sync도 Gemini가 route 권유해야 operator_request로 갈 단계).
- **seq 492 / seq 504 교훈 지속**: backend 쪽을 건드리게 되면 11+ green supervisor_missing cells + quiescent-path cell 비교표 필수.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 `tests/test_operator_request_schema.py` 단일 target file만 추가 수정.
