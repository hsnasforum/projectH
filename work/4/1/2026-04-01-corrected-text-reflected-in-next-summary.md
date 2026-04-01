# 2026-04-01 corrected_text reflected in next summary

## 변경 파일
- `storage/session_store.py`
- `tests/test_smoke.py`

## 사용 skill
- 없음

## 변경 이유
- operator가 요약 품질 축으로 전환, `corrected_text reflected in next summary only` 단일 슬라이스 지시.
- 기존: 사용자가 교정 제출(corrected_text)을 해도 active_context의 summary_hint는 원본 draft 그대로 → 후속 질문/재요약 시 원본 기준으로 응답.
- 교정 내용이 같은 세션 후속 요약에 반영되어야 사용자 교정이 의미 있어짐.

## 핵심 변경
- `storage/session_store.py` `record_correction_for_message`:
  - 교정 텍스트 저장 후, 같은 세션의 `active_context`에 `summary_hint`가 있으면 `corrected_text` 기반으로 갱신 (max 240자 truncation 유지)
  - `active_context`가 없는 세션에서는 무시 (안전 처리)
- `tests/test_smoke.py`:
  - `test_correction_updates_active_context_summary_hint`: 교정 후 summary_hint가 corrected_text로 바뀌는지 확인
  - `test_correction_without_active_context_does_not_fail`: active_context 없는 상태에서 교정해도 에러 없는지 확인

## 검증
- `python3 -m py_compile storage/session_store.py`: 통과
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`: 281 tests, OK (4.197s)
- `git diff --check -- storage/session_store.py tests/test_smoke.py`: 통과

## 남은 리스크
- 현재 구현은 교정 시점에 active_context가 있으면 무조건 summary_hint를 갱신함. 여러 문서를 번갈아 요약하는 시나리오에서는 교정 대상과 active_context 대상이 다를 수 있으나, 현재 MVP에서는 active_context가 항상 최신 요약에 해당하므로 실질적 위험 낮음.
- user-level memory나 broader personalization으로 확장하지 않음 (이번 라운드 범위 밖).
- docs sync는 이번 라운드에서 수행하지 않음. 다음 라운드에서 필요 시 동기화.
