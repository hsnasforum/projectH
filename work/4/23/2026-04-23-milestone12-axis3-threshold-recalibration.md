# 2026-04-23 Milestone 12 Axis 3 threshold recalibration

## 변경 파일
- `scripts/export_traces.py`
- `tests/test_export_utility.py`
- `work/4/23/2026-04-23-milestone12-axis3-threshold-recalibration.md`

## 사용 skill
- `security-gate`: 로컬 trace export 산출물의 quality subset 분류 기준이 바뀌므로 출력 파일과 원본 session JSON의 읽기/쓰기 경계를 확인했습니다.
- `finalize-lite`: handoff가 요구한 컴파일, unittest, export 실행, diff check 결과만 기준으로 완료 여부를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 한국어 closeout으로 남겼습니다.

## 변경 이유
- advisory(`CONTROL_SEQ: 931`)에서 실제 grounded-brief correction pair 137건의 `similarity_score`가 0.067–0.090에 분포한다고 확인했습니다.
- 기존 `_is_high_quality()` 하한 0.20은 sentence-level edit 기준이라 document-level grounded-brief rewrite를 모두 탈락시켜 high-quality 0건을 만들었습니다.

## 핵심 변경
- `scripts/export_traces.py`의 `_is_high_quality()` 하한을 `0.20`에서 `0.05`로 낮췄습니다.
- `tests/test_export_utility.py`에 grounded-brief empirical range(`0.067`, `0.075`, `0.090`)가 high-quality로 통과하고 `0.03`은 탈락하는 테스트를 추가했습니다.
- Axis 4 관련 promotion, `CorrectionStore`, feedback extension 등은 handoff 범위가 아니어서 구현하지 않았습니다.

## 검증
- `python3 -m py_compile scripts/export_traces.py tests/test_export_utility.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility -v 2>&1 | tail -5`
  - `Ran 46 tests in 0.042s`
  - `OK`
- `python3 scripts/export_traces.py`
  - `Exported 137 correction pairs → data/all_traces.jsonl`
  - `High-quality pairs: 137 → data/high_quality_traces.jsonl`
- `git diff --check -- scripts/export_traces.py tests/test_export_utility.py`
  - 통과
- `wc -l data/all_traces.jsonl data/high_quality_traces.jsonl`
  - `137 data/all_traces.jsonl`
  - `137 data/high_quality_traces.jsonl`

## 남은 리스크
- 이번 slice는 threshold recalibration만 수행했습니다. 실제 high-quality subset의 내용 품질 검토나 promotion asset 생성은 별도 handoff가 필요합니다.
- `scripts/export_traces.py`는 실행 시 `data/all_traces.jsonl`과 `data/high_quality_traces.jsonl`을 덮어씁니다. session 원본 JSON은 수정하지 않습니다.
- feedback 신호 0 gap과 Axis 4 범위는 이번 구현에서 다루지 않았습니다.
