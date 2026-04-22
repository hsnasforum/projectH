# 2026-04-23 Milestone 12 Axis 3 trace quality scoring

## 변경 파일
- `scripts/export_traces.py`
- `tests/test_export_utility.py`
- `work/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md`

## 사용 skill
- `security-gate`: 로컬 trace export가 `data/all_traces.jsonl`과 `data/high_quality_traces.jsonl`을 덮어쓰는 변경이므로 읽기/쓰기 경계와 산출물 위치를 확인했습니다.
- `finalize-lite`: handoff가 요구한 컴파일, unittest, export 실행 결과만 기준으로 완료 여부를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 한국어 closeout으로 남겼습니다.

## 변경 이유
- Milestone 12 Axis 3 handoff(`CONTROL_SEQ: 928`)에 따라 correction pair export에 품질 점수를 추가하고, 전체 valid pair와 high-quality subset을 분리해야 했습니다.
- 이후 personalization 검토에서 raw pair 전체와 품질 필터 subset을 구분해 볼 수 있어야 했습니다.

## 핵심 변경
- `scripts/export_traces.py`에서 `compute_correction_delta()`를 사용해 각 pair의 `similarity_score`, `change_types`, `is_high_quality`를 기록하도록 바꿨습니다.
- export output을 기존 `data/export_traces.jsonl` 대신 `data/all_traces.jsonl`과 `data/high_quality_traces.jsonl` 두 파일로 분리했습니다.
- `_is_high_quality(similarity_score)` helper를 추가해 `0.20 <= score <= 0.98` 범위를 high-quality로 판정하도록 했습니다.
- `tests/test_export_utility.py`에 moderate rewrite, trivial fix, complete rewrite, identical text delta-none 검증 4건을 추가했습니다.

## 검증
- `python3 -m py_compile scripts/export_traces.py tests/test_export_utility.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility -v 2>&1 | tail -16`
  - `Ran 45 tests in 0.041s`
  - `OK`
- `python3 scripts/export_traces.py`
  - `Exported 137 correction pairs → data/all_traces.jsonl`
  - `High-quality pairs: 0 → data/high_quality_traces.jsonl`
- `wc -l data/all_traces.jsonl data/high_quality_traces.jsonl`
  - `137 data/all_traces.jsonl`
  - `0 data/high_quality_traces.jsonl`

## 남은 리스크
- 현재 로컬 데이터 기준 high-quality subset이 0건입니다. 이는 필터 기준이나 기존 correction pair 품질 분포에 대한 후속 판단이 필요하다는 신호일 수 있지만, 이번 handoff 범위에서는 기준 조정이나 데이터 품질 분석을 진행하지 않았습니다.
- export script는 산출 JSONL 파일을 덮어씁니다. session 원본 JSON은 수정하지 않습니다.
- `data/all_traces.jsonl`과 `data/high_quality_traces.jsonl`은 검증 산출물이며 현재 `git status --short`에는 나타나지 않았습니다.
