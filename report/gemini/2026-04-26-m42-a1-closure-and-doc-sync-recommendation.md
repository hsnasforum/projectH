# Advisory Log: 2026-04-26-m42-a1-closure-and-doc-sync-recommendation

## 요약
M42 Axis 1 (Preference Status Filter) 구현 및 검증이 완료되었음을 확인했습니다. 현재 작업트리의 7개 변경 파일에 대한 커밋을 승인하며, 후속 작업으로 `ARCHITECTURE.md` 사양 동기화 및 `MILESTONES.md` 우선순위 조정을 권고합니다.

## 분석 및 판단
1. **검증 결과:**
   - `paused_count` 페이로드 추가 및 `PreferencePanel`의 상태별 필터 탭(전체/후보/활성/일시중지) 구현이 단위 테스트와 TypeScript 타입 체크를 통해 확인되었습니다.
   - `tests.test_web_app` 전체 스위트 미완료 및 Playwright 미실행 리스크가 있으나, 핵심 기능인 `list_preferences_payload` 카운트 로직은 `WebAppServiceTest`로 고정되었으므로 슬라이스 종료가 가능합니다.

2. **문서 격차 (Doc Drift):**
   - `PRODUCT_SPEC.md`와 `ACCEPTANCE_CRITERIA.md`는 이번 라운드에서 갱신되었으나, `ARCHITECTURE.md`에는 아직 `paused_count`와 필터 UI 사양이 반영되지 않았습니다.
   - `MILESTONES.md`의 "Next 3 Priorities" 항목 1(M42 A1), 2(watcher_core cleanup)가 완료 상태임에도 우선순위 목록에 잔존하여 진실의 원천(Truth) 혼선을 야기하고 있습니다.

3. **우선순위 결정:**
   - `GEMINI.md`의 "same-family current-risk reduction" 원칙에 따라, 기능 추가 이전에 누락된 아키텍처 사양을 보충하고 우선순위를 정돈하는 **Deep-Doc Sync**를 다음 슬라이스로 지정합니다.

## 권고 사항
- **RECOMMEND: commit the current 7-file bundle (M42 Axis 1).**
  - 대상 파일: `app/handlers/preferences.py`, `app/frontend/src/api/client.ts`, `app/frontend/src/components/PreferencePanel.tsx`, `docs/MILESTONES.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `tests/test_web_app.py`
- **RECOMMEND: implement Deep-Doc Sync and Priority Triage.**
  - `docs/ARCHITECTURE.md`에 M42 A1의 기술적 세부 사항(`paused_count` 페이로드, 필터 UI 구조) 반영.
  - `docs/MILESTONES.md` 우선순위 목록 갱신 (항목 1, 2 제거 및 차기 슬라이스 승격).

## Exact Slice 권고
- **TASK:** Deep-Doc Sync & Milestone Triage
- **FILES:** `docs/ARCHITECTURE.md`, `docs/MILESTONES.md`
- **CONTENT:** `ARCHITECTURE.md`에 `paused_count` 필드 및 `PreferencePanel` 탭 사양 추가; `MILESTONES.md` Next 3 Priorities 항목 1, 2 제거 및 Item 3 (E2E 환경 개선)을 Priority 1로 승격.
