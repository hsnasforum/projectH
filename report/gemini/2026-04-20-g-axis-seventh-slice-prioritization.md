# 2026-04-20 G-axis seventh slice prioritization

## 개요
- seq 456(G4)을 통해 지표 정확도(Accuracy)를 위한 `role_confidence` 튜닝이 완료됨.
- 현재 `tests/test_web_app.py`에서 `SQLiteSessionStore`의 메서드 누락(`_compact_summary_hint_for_persist`)으로 인해 27개의 에러가 발생하고 있으며, 지표 요약 문구 변경에 따른 assertion 실패도 존재함.
- "Maintenance/Stability" 축으로 전환하여 대규모 테스트 실패를 해결하고 시스템 안정성을 확보하고자 함.

## 판단
1. **current-risk reduction (우선순위 1):**
   - `SQLiteSessionStore`가 `SessionStore`의 `record_correction_for_message`를 에일리언싱하여 사용하지만, 내부에서 호출하는 `_compact_summary_hint_for_persist` 메서드가 `SQLiteSessionStore`에 정의되어 있지 않아 대량의 `AttributeError`가 발생함.
   - 이는 SQLite 저장소 기반의 모든 수정(correction) 기능을 마비시키는 심각한 유지보수 리스크임.
   - G6-sub1을 통해 이 메서드 패리티를 맞춤으로써 27개의 테스트 에러를 한 번에 제거할 수 있음.

2. **지표 정합성 완결 (Accuracy/Consumption 축의 마무리):**
   - `WebAppServiceTest`의 `test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_surface_canonical_slots_and_truthful_progress` 실패는 seq 441/447/450/453에서 진행한 요약 문구 변경의 결과임.
   - 이 테스트의 assertion을 실제 변경된 문구(`"한 가지 출처의 정보로만 확인됩니다"`)로 truth-sync하여 지표 개선 작업의 여파를 완전히 정리함.

3. **기타 후보 검토:**
   - **G3 (Search tuning):** 테스트가 대량으로 실패하는 상황에서의 전략 튜닝은 검증 신뢰도가 낮음. 안정화가 우선임.
   - **G5 (GUI backend tests):** `TestRuntimeStatusRead` 실패(11건)보다 `WebAppServiceTest` 실패(28건)의 규모와 파급력이 더 큼.
   - **G7..G10:** 내부 정리 및 어휘 정합성 작업은 핵심 기능 테스트가 green인 상태에서 진행하는 것이 바람직함.

## 권고 (RECOMMEND)
- **G6-sub1: SQLiteSessionStore method parity + WebAppServiceTest truth-sync**
- 구체적 범위:
  - `storage/sqlite_store.py::SQLiteSessionStore` 수정.
  - `SessionStore._compact_summary_hint_for_persist` 메서드를 `SQLiteSessionStore`에도 에일리언싱하거나 staticmethod로 추가.
  - `tests/test_web_app.py:14994` 부근의 `test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_surface_canonical_slots_and_truthful_progress` 수정.
  - `self.assertIn("단일 출처 상태", summary)`를 `"한 가지 출처의 정보로만 확인됩니다"`로 truth-sync.
  - `python3 -m unittest tests/test_web_app.py`를 통해 에러 수 감소 확인.

## 결론
G6-sub1을 통해 대규모 테스트 실패의 근본 원인인 메서드 누락을 해결하고, 지표 개선 작업의 잔여 truth-sync를 완료하여 프로젝트의 안정성 궤도를 회복할 것을 추천함.
