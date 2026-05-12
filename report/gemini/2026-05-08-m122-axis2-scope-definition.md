# 2026-05-08 M122 Axis 2 스코프 구체화 권고

## 조사 결과 요약

### 1. 현재 재조사 메커니즘 확인
현재 시스템은 두 단계의 재조사 경로를 가지고 있음:
- **백엔드 (Auto-trigger)**: `agent_loop.py:_build_entity_second_pass_queries`가 1차 검색 후 `CoverageStatus.STRONG`이 아닌 슬롯들에 대해 즉시 2차 쿼리를 생성하여 실행함.
- **UI (User-trigger)**: `agent_loop.py:_build_entity_reinvestigation_suggestions`가 응답 하단에 "X 개발사 검색해봐" 같은 제안 버튼을 생성함.

### 2. WEAK 상태의 모호성
현재 `CoverageStatus.WEAK`는 아래 두 경우를 모두 포함함:
- 신뢰 소스가 1개인 경우 (단일 출처 합의 필요)
- 신뢰 소스가 0개이나, 비신뢰 소스(커뮤니티 등)에서 아이템이 발견된 경우 (신뢰 소스 탐색 필요)

이로 인해 `_build_entity_second_pass_queries`의 우선순위(tier) 시스템에서 "아이템이 아예 없는 MISSING"보다 "비신뢰 아이템만 있는 WEAK"이 더 높은 우선순위를 가지게 되는데, 이때 `WEAK` 내부의 세분화가 없어 1개 신뢰 소스가 있는 경우와 동일하게 취급되는 한계가 있음.

## 권고 사항

### 1. CoverageStatus.UNRESOLVED 신설
`WEAK`를 세분화하여 `UNRESOLVED` 상태를 추가할 것을 권장함.
- `STRONG`: 신뢰 소스 2개 이상 합의.
- `WEAK`: 신뢰 소스 1개. (기존 단일 출처)
- `UNRESOLVED`: 신뢰 소스 0개이나 후보 아이템 존재. (신규)
- `MISSING`: 아이템 없음.

### 2. 재조사 전략 차별화
- `UNRESOLVED` 슬롯: 후보 아이템(untrusted)의 값을 키워드로 활용하여 "공식/위키" 등 신뢰 소스를 찾는 Probe 쿼리를 최우선으로 생성.
- `WEAK` 슬롯: 이미 1개의 신뢰 소스가 있으므로, 다른 신뢰 소스를 추가로 찾는 Confirmation 쿼리 생성.

### 3. 단계적 구현 (Implement Slice)
- **Slice 1 (Backend)**: `contracts.py`, `web_claims.py`, `agent_loop.py`의 상태 정의 및 판정 로직 고도화.
- **Slice 2 (Backend logic improvement)**: `_build_entity_second_pass_queries`의 쿼리 생성 품질 개선.
- **Slice 3 (UI)**: `[미해결]` 또는 `[추가 확인 필요]` 태그 및 안내 문구 UI 반영.

## 결정 제안

**RECOMMEND: implement m122_axis2_backend_unresolved_separation**
- **대상**: `core/contracts.py`, `core/web_claims.py`, `core/agent_loop.py`
- **내용**: `UNRESOLVED` 상태 도입 및 백엔드 2차 pass 쿼리 생성 로직 연동.
- **근거**: 상태 구분이 명확해야 재조사 쿼리의 목적(Probe vs Confirm)을 최적화할 수 있으며, 이는 유저에게 더 정확한 웹 조사 품질을 제공하는 기반이 됨.
