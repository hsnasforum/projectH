# Advisory Log: 2026-04-28 — M61 완료 및 M62 방향 권고

## 개요
M61 Axis 1+2 완료를 통해 `GET /api/corrections/summary` 엔드포인트와 E2E 격리 시나리오가 확보됨. 다음 마일스톤 M62의 방향으로 교정 통계의 프론트엔드 가시화(Visibility)를 권고함.

## 분석
- **성과**: 백엔드에서 전체 교정 수, 상태별 통계, 상위 반복 패턴(fingerprint)을 집계하는 기능이 완성되었으며, E2E 테스트를 통해 응답 규격이 고정됨.
- **현 상태**: 데이터는 존재하지만 브라우저 UI(`app.web`)에서는 아직 이 통계를 확인할 수 없는 "Headless" 상태임.
- **리스크**: 분석 데이터가 사용자나 운영자에게 노출되지 않으면 M61의 가치가 실현되지 않음. `TASK_BACKLOG`의 "physical correction analytics" 단계를 완성하기 위해서는 시각적 피드백이 필수적임.

## 권고 사항
`RECOMMEND: implement M62 Axis 1 — correction summary frontend 표시`

### 권고 이유
1. **Visibility Completion**: M61에서 구축한 백엔드 데이터를 UI(`PreferencePanel`)에 통합하여 교정 루프의 효율성을 직접 확인할 수 있게 함.
2. **Same-family Improvement**: 선호도(Preference)와 교정(Correction)은 동일한 "Reviewed-Memory" 계열이며, 이미 완성된 Preference 통계 UI 근처에 Correction 통계를 배치하는 것이 아키텍처적으로 일관됨.
3. **Operational Value**: 운영자가 현재 시스템에 누적된 교정 패턴의 규모를 파악하고, 후속 "Validation" 작업을 판단하는 기초 자료로 활용 가능함.

### 구현 슬라이스
- `app/frontend/src/api/client.ts`: `fetchCorrectionSummary()` 추가 및 타입 정의.
- `app/frontend/src/components/PreferencePanel.tsx`: `PreferenceAudit` 섹션 하단 또는 별도 영역에 교정 통계(전체/활성/패턴 수) 렌더링.

## 결론
M61의 백엔드 성과를 UI로 연결하여 "Visibility" 루프를 완성하는 M62 Axis 1 진행을 강력히 권고함.
