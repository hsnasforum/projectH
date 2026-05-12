# Advisory Log: 2026-04-28 — M67 완료 및 M68 방향 권고

## 개요
M67 Axis 1+2 완료를 통해 최근 교정 기록 목록(Correction List View)이 시각화됨에 따라, 운영자가 개별 교정의 흐름을 파악하고 반복 패턴을 승인/무시할 수 있는 체계가 완성됨. 다음 마일스톤 M68에서는 승인된 교정 패턴을 실제 선호도(Preference)로 승격시키는 "패턴 기반 승격(Pattern-level Promotion)"을 권고함.

## 분석
- **성과**: M61-M67을 통해 교정 통계 집계, 상위 패턴 노출, 개별 기록 목록, 승인/무시 조작이 모두 완료됨. "가시성(Visibility)"과 "검증(Validation)" 레이어가 탄탄하게 구축됨.
- **현 상태**: 운영자가 특정 패턴을 `CONFIRMED`로 승격시켰더라도, 이것이 실제 모델 응답에 영향을 주는 `PreferenceRecord`로 자동 전환되는 경로가 부족함. 현재는 `promote_from_corrections` (2개 이상의 세션 감지 시 자동)나 `record_reviewed_candidate_preference` (리뷰 큐 수락 시) 경로에 의존하고 있음.
- **기회**: 운영자가 명시적으로 승인한(`CONFIRMED`) 패턴을 즉시 `PROMOTED` 상태로 전환하고, 이를 기반으로 `PreferenceRecord`를 생성하는 명시적 승격 경로를 추가하여 "Reviewed-Memory" 루프의 최종 단계를 완성할 수 있음.

## 권고 사항
`RECOMMEND: implement M68 Axis 1 — Pattern-level promotion to Preference`

### 권고 이유
1. **Closing the Loop**: 교정에서 시작된 데이터가 검증을 거쳐 선호도로 정착되는 전체 생명주기(Lifecycle)를 완성함.
2. **Operational Control**: 자동 승격 조건(2개 이상의 세션 등)을 충족하지 않더라도, 운영자가 판단하기에 중요한 패턴을 즉시 시스템 지식으로 편입시킬 수 있는 강력한 도구를 제공함.
3. **Data Integrity**: 기존의 `promote_from_corrections` 로직과 통합하여, 승격된 패턴이 `PreferenceRecord`에서 올바른 출처 기록(Source Refs)을 갖도록 보장함.

### 구현 슬라이스
- **Storage**: `CorrectionStore` 및 `SQLiteCorrectionStore`에 `promote_by_fingerprint()` 추가.
- **Backend**: `POST /api/corrections/promote-pattern` 엔드포인트 추가. 승격 시 `PreferenceStore.record_reviewed_candidate_preference()`를 호출하여 실제 선호도 레코드 생성.
- **Frontend**: `PreferencePanel.tsx`에서 `CONFIRMED` 상태의 패턴 옆에 "승격(Promote)" 버튼 표시.

## 결론
검증된 데이터를 시스템의 실제 지능으로 변환하는 M68 Axis 1 진행을 강력히 권고함.
