# 2026-04-30 M107 방향 제언: 교정 이력 페이지네이션 및 오프셋 조회 (Gemini)

## 1. 개요
M106에서 도입된 `limit` 파라미터와 '더 보기' UI는 대량의 교정 이력을 효율적으로 조회하기 위한 첫 단추였습니다. M107에서는 이를 완성하여, 특정 시점 이후의 데이터를 정확히 가져올 수 있는 '페이지네이션(Pagination)' 계약을 확정하는 방향을 제언합니다.

## 2. 조사 및 판단

### 2.1. M106 성과와 M107의 필요성
- **성과:** 하드코딩된 조회 제한을 풀고, 사용자가 원하는 만큼 리스트를 확장할 수 있는 기초를 마련함.
- **한계:** 현재 '더 보기' 버튼을 눌러도 항상 처음 N개만 가져오거나(정적 리밋), 프런트엔드에서 수동으로 리밋을 키우는 방식은 데이터가 많아질수록 서버 부하와 클라이언트 메모리 점유율을 높임.
- **판단:** `offset` 파라미터가 추가되어야만 진정한 의미의 '이전 데이터 탐색'이 가능해지며, 이는 Evidence Visibility 아크의 마지막 기술적 조각입니다.

### 2.2. 선택 (Choice A vs B)
- **Choice A (Pagination):** 백엔드 스토어 계층이 이미 지원할 준비가 되어 있는 `offset`을 노출하여, API를 표준화하고 UI 안정성을 높이는 가장 합리적인 연속성임. (선정)
- **Choice B (Other):** 현재 교정 이력 도구가 갖춰진 상태에서 다른 축(Axis switch)으로 넘어가는 것보다, 시작한 기능을 완성(Close same-family)하는 것이 `GEMINI.md` 판단 기준에 부합함.

## 3. 권고 (Recommendation)

**RECOMMEND: implement Correction History Pagination (Choice A)**

### 기술/제품적 이유:
1. **API 계약의 완결:** `limit`과 `offset`의 쌍은 API 설계의 표준이며, 이를 통해 무한 스크롤이나 페이지 이동 등 다양한 UI 패턴에 대응할 수 있는 범용성을 확보함.
2. **성능 최적화:** 서버에서 필요한 만큼만 잘라서 전송함으로써 대규모 데이터셋에서도 응답 속도와 메모리 효율을 유지함.
3. **사용자 경험(UX):** 수백 개의 교정 이력이 쌓여도 사용자가 과거의 학습 근거를 유실하지 않고 끝까지 추적할 수 있는 수단을 제공함.

### 실행 가이드:
- **Backend:** `CorrectionHandlerMixin.get_correction_list`에 `offset=0` 인자 추가. `storage` 계층의 `list_filtered`에 `offset` 전달 보강.
- **Web:** `GET /api/corrections/list?offset=N&limit=M` 라우팅 파라미터 처리.
- **Frontend:** `PreferencePanel.tsx`에서 '더 보기' 클릭 시 현재 리스트의 길이를 `offset`으로 사용하여 다음 배치를 호출하도록 수정.
- **Branch:** `feat/m106-correction-search-expansion` 베이스에서 `feat/m107-correction-history-pagination` 생성.

---
**STATUS:** advice_ready
**CONTROL_SEQ:** 1476
