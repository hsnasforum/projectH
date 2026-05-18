# 2026-04-30 M108 방향 제언: 선호도 검색 UI 및 관리 가시성 강화 (Gemini)

## 1. 개요
M98~M107에 걸친 'Evidence Visibility(근거 가시성)' 아크를 통해 교정 이력(Correction History)의 상세 조회, 검색, 필터링, 페이지네이션이 완비되었습니다. M108에서는 이 성과를 'Outcome(결과물)'인 선호도(Preference) 영역으로 확장하여, 관리 도구로서의 완결성을 높이는 'Preference Visibility Parity' 방향을 제언합니다.

## 2. 조사 및 판단

### 2.1. 현재 구현의 불균형 (UX Asymmetry)
- **교정 이력:** 검색, 필터, 페이지네이션, 상세 조회가 모두 가능하여 대량의 데이터 관리가 용이함.
- **선호도 리스트:** 상태별 탭(Tabs)은 제공되나, 선호도가 늘어남에 따라 특정 선호(description)를 찾기 위한 '텍스트 검색' 수단이 없음.
- **상태:** M97 자동 활성화 기능 등으로 인해 사용자가 인지하지 못한 채 생성되는 선호도가 늘어날 수 있으나, 이를 효과적으로 찾아내어 수정(M104)하거나 삭제(M102)하기 위한 검색 UI가 부재함.

### 2.2. 선택 (Choice A vs B)
- **Choice A (Correction Polish):** 날짜 정렬이나 네비게이션은 유용하지만, 이미 충분히 고도화된 영역의 미세한 개선에 해당함.
- **Choice B (Preference Visibility):** 선호도 관리의 핵심인 '검색' 기능을 추가하여 교정 이력 도구와의 기능적 대칭(Parity)을 맞추는 것이 더 높은 제품 가치를 가짐. (선정)

## 3. 권고 (Recommendation)

**RECOMMEND: implement Preference Search & List Visibility Parity (Choice B)**

### 기술/제품적 이유:
1. **관리 효율성 제고:** 선호도 설명(description) 검색을 통해 사용자가 특정 업무 규칙(예: "존댓말 사용", "JSON 포맷")과 관련된 선호를 즉시 찾아 관리할 수 있게 함.
2. **도구 간 일관성:** 교정 이력 UI에서 익힌 검색/필터 사용 패턴을 선호도 리스트에서도 동일하게 적용할 수 있도록 하여 학습 비용을 줄임.
3. **아크의 확장:** '근거'의 가시성을 넘어, 그 근거로 인해 도출된 '지식(선호도)'의 검색 가능성을 확보함으로써 전체 학습 루프의 관리 인터페이스를 완성함.

### 실행 가이드:
- **Backend:** `list_preferences_payload`에 `query` 파라미터를 추가하여 `description` 기반 서버측 필터링 지원 (또는 현재처럼 전체 페이로드를 보내는 경우 프런트엔드 클라이언트측 검색 구현).
- **Frontend:** `PreferencePanel.tsx`의 선호도 섹션 상단에 검색 입력창 추가. 검색어에 따라 `filteredPreferences` 동적 필터링.
- **Branch:** `feat/m107-correction-history-pagination` 베이스에서 `feat/m108-preference-visibility-parity` 생성.

---
**STATUS:** advice_ready
**CONTROL_SEQ:** 1480
