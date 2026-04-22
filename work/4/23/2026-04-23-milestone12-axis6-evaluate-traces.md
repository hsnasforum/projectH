# 2026-04-23 Milestone 12 Axis 6 evaluate traces

## 변경 파일
- `storage/session_store.py`
- `scripts/evaluate_traces.py`
- `tests/test_export_utility.py`
- `tests/test_evaluate_traces.py`
- `work/4/23/2026-04-23-milestone12-axis6-evaluate-traces.md` (이 파일)

## 사용 skill
- `security-gate`: session trace payload 읽기와 로컬 JSONL 평가 산출물 경계를 확인했다.
- `finalize-lite`: 지정 검증 결과, doc-sync 필요 여부, `/work` closeout 준비 상태를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- Milestone 12 Axis 6 handoff에 따라 correction trace에 기존 `feedback` 필드를 포함하고, `data/all_traces.jsonl` 기반 metric baseline report를 출력하는 평가 스크립트를 추가했다.
- `preference_store.py`, `correction_store.py`, 계약 파일, `.pipeline` control slot은 수정하지 않았다.

## 핵심 변경
- `SessionStore.stream_trace_pairs()` yield dict에 `feedback: msg.get("feedback")`를 추가했다.
- `scripts/evaluate_traces.py`를 추가해 correction pair 수, high-quality 수, feedback-enriched 수, similarity/length 통계, model-layer justification verdict를 출력한다.
- `tests/test_export_utility.py`에 trace pair가 `feedback` key를 항상 포함하는지 확인하는 테스트를 추가했다.
- `tests/test_evaluate_traces.py`에 JUSTIFIED, INSUFFICIENT DATA, empty input, missing file 경로 테스트 4개를 추가했다.
- `scripts/export_traces.py` 실행 결과 생성되는 `data/*.jsonl` 파일들은 `.gitignore`의 `data/*` 규칙으로 추적되지 않는 로컬 산출물임을 확인했다.

## 검증
- `python3 -m py_compile storage/session_store.py scripts/evaluate_traces.py tests/test_export_utility.py tests/test_evaluate_traces.py`
  - 통과, 출력 없음
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v 2>&1 | tail -5`
  - `Ran 56 tests in 0.054s`
  - `OK`
- `python3 scripts/export_traces.py`
  - `Exported 137 correction pairs → data/all_traces.jsonl`
  - `High-quality pairs: 137 → data/high_quality_traces.jsonl`
  - `Preference assets: 23 → data/preference_assets.jsonl`
- `python3 scripts/evaluate_traces.py`
  - `Correction pairs:    137`
  - `High-quality:        137 (100%)`
  - `Feedback-enriched:   0`
  - `Model layer justification: JUSTIFIED`
- `git diff --check -- storage/session_store.py tests/test_export_utility.py`
  - 통과, 출력 없음
- `git diff --check -- storage/session_store.py scripts/evaluate_traces.py tests/test_export_utility.py tests/test_evaluate_traces.py`
  - 통과, 출력 없음
- `git check-ignore -v data/all_traces.jsonl data/high_quality_traces.jsonl data/preference_assets.jsonl`
  - `.gitignore:21:data/*`로 3개 로컬 산출물이 ignore됨을 확인했다.

## 남은 리스크
- 현재 로컬 데이터 기준 feedback-enriched correction pair는 0건이다. 이번 slice는 필드 전달과 평가 리포트 기반만 추가했고, 새 feedback 수집 정책이나 품질 판정 기준 조정은 하지 않았다.
- 새 평가 스크립트는 `data/all_traces.jsonl`이 최신이라는 전제에서 읽는다. 최신 수치를 보려면 `scripts/export_traces.py`를 먼저 실행해야 한다.
- 문서 동기화는 handoff 범위에 포함되지 않아 수행하지 않았다. 이번 구현 사실은 이 `/work` closeout에만 기록했다.
