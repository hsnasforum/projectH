# 2026-04-16 reviewed-memory family 종료 및 durable preference memory 축 전환 중재 보고서

## 결정 요약
다음 구현 슬라이스로 **new quality axis: Durable preference memory local store schema and persistence (Phase 2 진입)**를 추천합니다.

## 중재 배경
- `work/4/16/2026-04-16-reviewed-memory-aggregate-record-backed-historical-basis-clarity.md` 라운드를 통해 동일 세션(same-session) aggregate의 가독성과 상태 보존 계약이 충분히 닫혔습니다.
- `reviewed-memory` 가족은 이제 검토 큐, aggregate 트리거, transition 기록(emitted/applied/result/active), 중단/되돌리기/충돌 확인, 그리고 supersession 생존 및 UI 레이블링까지 포함하는 성숙한 루프를 갖추었습니다.
- `GEMINI.md`의 우선순위 원칙에 비추어 볼 때, 동일 가족 내의 미세한 개선(diminishing returns)보다는 `docs/MILESTONES.md`에서 예고된 다음 단계인 "Durable Preference Memory"로의 축 전환(Axis Switch)이 진척의 정직성(truthfulness) 측면에서 더 우월합니다.

## 기술적 권고 사항
1. **Durable Preference Store 정의**:
   - 현재 세션에만 머물러 있는 `durable_candidate`와 `candidate_review_record`를 넘어서, 세션을 가로질러 유지될 수 있는 `durable_preference_memory`의 첫 번째 로컬 저장소 스키마를 정의합니다.
2. **구현 범위 (Phase 2.1)**:
   - 검토 수락된(`accepted`) 후보들을 별도의 로컬 JSON 저장소(예: `data/preferences/`)에 저장하거나 로드할 수 있는 기본 영속성 레이어를 구현합니다.
   - 이번 단계에서는 실제 응답 생성 시의 주입(injection)보다는, "수락된 후보가 세션 종료 후에도 로컬 파일로 안전하게 기록되고 추적되는가"에 집중하여 무결성 리스크를 관리합니다.
3. **검증 전략**:
   - 단위 테스트 또는 Playwright smoke test를 통해, 특정 세션에서 `accept`된 검토 후보가 로컬 preference store 파일에 올바른 스키마로 기록되는지 확인합니다.

## 결론
이 슬라이스는 `projectH`가 단순한 '세션 보조 도구'에서 '사용자로부터 배우는 로컬 에이전트'로 진화하는 중요한 전환점입니다. `reviewed-memory`의 성과를 기반으로 더 넓은 지평(Milestone 4, Phase 2)으로 나아가는 것을 추천합니다.
