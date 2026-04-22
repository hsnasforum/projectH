# 2026-04-23 Milestone 12 Axis 5 preference visibility

## 변경 파일
- `scripts/audit_traces.py`
- `scripts/export_traces.py`
- `tests/test_export_utility.py`
- `work/4/23/2026-04-23-milestone12-axis5-preference-visibility.md` (이 파일)

## 사용 skill
- `security-gate`: 로컬 JSONL export 쓰기와 `PreferenceStore` 읽기 경계를 확인했다.
- `finalize-lite`: 지정 검증, doc-sync 필요 여부, `/work` closeout 준비 상태를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- Milestone 12 Axis 5 handoff에 따라 기존 `PreferenceStore`의 CANDIDATE/ACTIVE 선호 데이터를 audit/export pipeline에서 볼 수 있게 했다.
- `storage/session_store.py`, `storage/preference_store.py`, `storage/correction_store.py`, 계약 파일은 수정하지 않았다.

## 핵심 변경
- `scripts/audit_traces.py`가 `PreferenceStore.get_candidates()`와 `get_active_preferences()`를 읽어 summary에 `Preferences: candidate=N, active=M`을 출력한다.
- `scripts/export_traces.py`가 기존 correction-pair export는 유지하면서 `data/preference_assets.jsonl`에 candidate + active preference record를 JSONL로 쓴다.
- `tests/test_export_utility.py`에 preference export 경로와 candidate/active 직렬화 포함 여부를 확인하는 테스트 2개를 추가했다.
- export 실행 결과 현재 로컬 데이터 기준 `data/preference_assets.jsonl`은 23라인으로 생성됐다.

## 검증
- `python3 -m py_compile scripts/audit_traces.py scripts/export_traces.py tests/test_export_utility.py`
  - 통과, 출력 없음
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets -v 2>&1 | tail -5`
  - `Ran 51 tests in 0.056s`
  - `OK`
- `python3 scripts/audit_traces.py 2>&1 | grep "Preferences:"`
  - `Preferences:       candidate=23, active=0`
- `python3 scripts/export_traces.py 2>&1 | grep "Preference assets:"`
  - `Preference assets: 23 → data/preference_assets.jsonl`
- `git diff --check -- scripts/audit_traces.py scripts/export_traces.py tests/test_export_utility.py`
  - 통과, 출력 없음

## 남은 리스크
- handoff 범위 밖인 `stream_trace_pairs()` feedback metadata 확장과 `_is_high_quality` feedback flag 조정은 구현하지 않았다.
- `data/preference_assets.jsonl`은 export utility 실행 산출물이며 현재 작업 트리 status에는 추적 변경으로 나타나지 않는다.
- `PreferenceStore` record 품질 평가나 downstream 모델 사용은 이번 slice 범위 밖이다.
