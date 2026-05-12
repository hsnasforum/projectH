# 2026-04-30 M109 방향 제언: 선호도 리스트 페이지네이션 및 성능 최적화 (Gemini)

## 1. 개요
M106~M107을 통해 교정 이력(Correction History)의 검색과 페이지네이션이 완비되었고, M108에서 선호도(Preference) 검색 기능이 추가되었습니다. M109에서는 이 '기능적 대칭(Functional Parity)' 아크의 마지막 조각인 '선호도 페이지네이션'을 구현하여, 대규모 선호도 데이터셋에서도 안정적인 관리 성능을 확보하는 방향을 제언합니다.

## 2. 조사 및 판단

### 2.1. 현재 구현의 한계
- **데이터 로드 비효율:** 현재 `list_preferences_payload`는 서버의 모든 선호도 데이터를 한 번에 가져와 프런트엔드에서 처리합니다. 선호도가 수백 건 이상 쌓일 경우 초기 로딩 속도 저하와 브라우저 메모리 부하가 예상됩니다.
- **UI 불일치:** 교정 이력 리스트는 '더 보기(Show More)' 버튼을 통한 점진적 로딩을 지원하는 반면, 선호도 리스트는 전체 데이터를 한꺼번에 노출하고 있어 사용자 경험의 일관성이 부족합니다.

### 2.2. 선택 (Choice A vs B)
- **Choice A (Preference Pagination):** 교정 이력 도구(M107)와의 대칭성을 완성하고 성능적 리스크를 선제적으로 제거하는 'Same-family' 개선입니다. (선정)
- **Choice B (Other Axis):** Review Queue 강화 등 다른 아크로 넘어가는 것도 가치가 있으나, 현재 진행 중인 '관리 도구의 완결성' 아크를 먼저 닫는(Close family) 것이 시스템 안정성 측면에서 유리합니다.

## 3. 권고 (Recommendation)

**RECOMMEND: implement Preference List Pagination (Choice A)**

### 기술/제품적 이유:
1. **확장성(Scalability) 확보:** 사용자가 시스템을 오래 사용할수록 학습된 지식(선호도)은 계속 늘어납니다. 서버-사이드 페이지네이션은 데이터 규모와 무관하게 일정한 응답성을 보장합니다.
2. **기능적 대칭 완성:** 검색(M108)과 페이지네이션(M109)이 결합됨으로써, 선호도 관리 UI는 교정 이력 UI와 동일한 수준의 성숙도를 갖추게 됩니다.
3. **사용자 경험 일관성:** '더 보기' UI를 선호도 리스트에도 적용하여 제품 전반의 데이터 탐색 패턴을 통일합니다.

### 실행 가이드:
- **Backend:** `list_preferences_payload`에 `limit`, `offset` 파라미터 추가. `preference_store.list_all`에서 슬라이싱 지원 보강.
- **Web:** `GET /api/preferences` 요청 시 쿼리 파라미터를 핸들러로 전달.
- **Frontend:** `PreferencePanel.tsx`에서 선호도 리스트 하단에 '더 보기' 버튼 추가 및 `offset` 기반 점진적 로딩 로직 구현.
- **Branch:** `feat/m108-preference-visibility-parity` 베이스에서 `feat/m109-preference-pagination` 생성.

---
**STATUS:** advice_ready
**CONTROL_SEQ:** 1484
