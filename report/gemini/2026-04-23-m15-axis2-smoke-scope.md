# Advisory Log: M15 Axis 2 - Quality Integration Smoke Tests Scope

## 개요
- **일시**: 2026-04-23
- **요청**: M15 Axis 2 (Quality Integration Smoke Tests)의 정확한 범위 및 시나리오 정의
- **상태**: M14 품질 배지 UI와 M15 Axis 1 SQLite quality parity가 완료되었으나, 브라우저 레이어에서의 품질 기능 검증(Playwright)이 부재함.

## 분석 및 판단
1.  **검증 대상**: 
    - `PreferencePanel.tsx`: `quality_info.is_high_quality`에 따른 `고품질` 배지 노출.
    - `ChatArea.tsx`: `highQualityReviewCount`에 따른 `리뷰 N건 · 고품질 M건` 배지 노출.
2.  **테스트 전략**: 
    - **격리(Isolation)**: `page.request`를 사용해 특정 품질 점수를 가진 데이터를 주입함으로써 세션 간 간섭 없이 빠르게 렌더링 조건을 충족함.
    - **E2E 흐름(Flow)**: 실제 사용자의 교정(Correction) 행위가 품질 점수 계산과 헤더 카운트 업데이트로 이어지는 전체 루프를 검증함.
    - **정합성(Parity)**: SQLite 설정을 통해 백엔드 스토리지 종류와 무관하게 동일한 UI 계약이 유지되는지 확인함.
3.  **파일 구성**: 
    - 기존 `e2e/tests/web-smoke.spec.mjs`에 시나리오를 추가하여 관리 부담을 줄이고 기존 인프라를 재사용함.

## 권고 시나리오 (RECOMMEND)

### Scenario 1: PreferencePanel 고품질 배지 노출
- **목적**: 백엔드가 제공하는 `quality_info`가 설정창 UI에 정확히 반영되는지 검증.
- **준비**: `page.request.post('/api/preference', ...)`를 사용해 `avg_similarity_score: 0.5` (고품질 범위)인 활성 선호를 주입.
- **확인**: 사이드바의 '선호 기억' 섹션을 열고 해당 선호 항목 옆에 `고품질` 텍스트가 보이는지 확인.

### Scenario 2: ChatArea 헤더 고품질 리뷰 카운트
- **목적**: 교정 제출 -> 후보 기록 -> 헤더 카운트 업데이트로 이어지는 실시간 품질 통합 흐름 검증.
- **준비**: 새 세션 시작 -> 메시지 전송 -> 0.05~0.98 사이의 유사도를 갖는 교정 제출 -> '재사용 확인' 버튼 클릭.
- **확인**: 상단 헤더의 리뷰 배지 내에 `· 고품질 1건` 텍스트가 나타나는지 확인 (`.quality-count` 셀렉터 사용).

### Scenario 3: 백엔드 정합성 (SQLite Parity)
- **목적**: SQLite 스토리지 사용 시에도 위 품질 UI가 동일하게 작동하는지 검증.
- **실행**: `e2e/playwright.sqlite.config.mjs` 설정을 사용하여 위 시나리오들을 포함한 `web-smoke.spec.mjs` 재실행.

## 기대 효과
- M14 품질 통합 기능의 퇴보(Regression) 방지.
- JSON/SQLite 통합 스토리지 레이어의 UI 호환성 보장.
