# 2026-04-23 Milestone 12 Axis 2 trace export utility

## 변경 파일
- `storage/session_store.py`
- `scripts/export_traces.py`
- `tests/test_export_utility.py`
- `work/4/23/2026-04-23-milestone12-axis2-trace-export-utility.md`

## 사용 skill
- `security-gate`: 로컬 session trace를 읽고 `data/export_traces.jsonl`로 내보내는 변경이라 읽기/쓰기 경계와 저장 위치를 확인했습니다.
- `finalize-lite`: handoff가 요구한 세 검증 명령과 변경 파일 범위만 기준으로 완료 여부를 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 명령, 남은 리스크를 한국어 closeout으로 남겼습니다.

## 변경 이유
- Milestone 12 Axis 2 handoff(`CONTROL_SEQ: 924`)에 따라 grounded-brief correction pair를 JSONL로 내보내는 로컬 export utility가 필요했습니다.
- Axis 1의 trace count baseline을 실제 후보 데이터 파일로 변환해 이후 personalization 검토의 입력으로 쓸 수 있게 해야 했습니다.

## 핵심 변경
- `SessionStore.stream_trace_pairs()` generator를 추가해 전체 session JSON에서 `grounded_brief` source message의 `original_response_snapshot.draft_text`와 `corrected_text`를 `prompt`/`completion` pair로 순회하도록 했습니다.
- `scripts/export_traces.py`를 추가해 `data/export_traces.jsonl`에 correction pair를 JSONL로 저장하고 export count를 출력하도록 했습니다.
- script 경로 직접 실행(`python3 scripts/export_traces.py`)이 가능하도록 repo root를 `sys.path`에 추가했습니다.
- `tests/test_export_utility.py`에 prompt/completion 출력, empty store, newline 보존, corrected_text 없는 message skip을 검증하는 4개 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile storage/session_store.py scripts/export_traces.py tests/test_export_utility.py`
  - 통과
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility -v 2>&1 | tail -16`
  - `Ran 41 tests in 0.038s`
  - `OK`
- `python3 scripts/export_traces.py`
  - `Exported 137 correction pairs → data/export_traces.jsonl`
- `wc -l data/export_traces.jsonl`
  - `137 data/export_traces.jsonl`

## 남은 리스크
- 이번 slice는 export utility만 추가했습니다. export된 JSONL의 품질 평가, threshold 판단, 학습/개인화 파이프라인 연결은 handoff 범위가 아니어서 진행하지 않았습니다.
- `scripts/export_traces.py`는 로컬 `data/export_traces.jsonl`을 덮어씁니다. 실행 자체는 명시 명령으로만 수행되며 session 원본 JSON은 수정하지 않습니다.
- `data/export_traces.jsonl`은 검증 명령의 산출물이며 현재 `git status --short`에는 나타나지 않았습니다.
