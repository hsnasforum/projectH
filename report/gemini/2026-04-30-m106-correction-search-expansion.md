# 2026-04-30 M106 방향 제언: 교정 이력 검색 UI 및 리스트 확장 (Gemini)

## 1. 개요
M105에서 도입된 '상태 필터'를 통해 교정 이력의 분류가 가능해졌습니다. M106에서는 'Visibility(가시성)' 아크의 실질적인 완성을 위해, 백엔드 API가 이미 지원하고 있는 '텍스트 검색' 기능을 UI에 연결하고, 하드코딩된 조회 제한을 완화하는 방향을 제언합니다.

## 2. 조사 및 판단

### 2.1. 잔여 UX 부채 (UX Debt)
- **검색 기능 유실:** `app/handlers/corrections.py`의 `get_correction_list`는 이미 `query` 파라미터를 통해 텍스트 검색을 지원하지만, 현재 UI(`PreferencePanel.tsx`)에는 이를 활용할 입력 필드와 상태 관리가 없습니다.
- **데이터 병목:** 현재 백엔드 핸들러는 `limit=5`로 고정되어 있어, 필터링을 하더라도 전체 이력을 확인하기 어렵습니다. 이는 M104 제언(seq 1464)에서 언급된 "너비(Width)의 확장"이 아직 미완성임을 의미합니다.

### 2.2. M106 선정 근거
- **A/B 테스트 중 선택:** `advisory_request`의 후보군 중 '텍스트 검색'은 이미 백엔드 준비가 완료된 저비용 고효율 작업입니다.
- **아크의 완결:** 검색(Search) + 필터(Filter) + 상세(Detail)가 결합되어야만 사용자가 선호도의 근거를 능동적으로 추적할 수 있는 'Evidence Visibility' 아크가 비로소 제품으로서 가치를 가집니다.

## 3. 권고 (Recommendation)

**RECOMMEND: implement Correction History Text Search & List Expansion**

### 기술/제품적 이유:
1. **검색 연결:** UI에 검색창을 배치하고 `correctionQuery` 상태를 백엔드 `query` 파라미터로 전달하여, 수많은 교정 중 특정 키워드(예: 특정 단어 교체 이력)를 즉시 찾을 수 있게 합니다.
2. **조회 제한 완화:** 핸들러의 하드코딩된 `limit=5`를 상향(예: 20)하거나 파라미터화하고, 프런트엔드에서 '더 보기(See More)' 버튼을 통해 추가 데이터를 로드할 수 있는 Seam을 마련합니다.
3. **신뢰성 검증의 편의성:** 사용자가 선호도를 수정(M104)하거나 신뢰도 토글(M103)을 결정할 때, 관련 있는 과거 교정 사례들을 검색하여 빠르게 검토할 수 있는 환경을 제공합니다.

### 실행 가이드:
- **Backend:** `CorrectionHandlerMixin.get_correction_list`의 `limit` 파라미터 하드코딩 제거 및 `web.py` 전달 보강.
- **Frontend:** `PreferencePanel.tsx`에 검색 입력 UI 추가, `load` 호출 시 `query` 파라미터 연동, 리스트 하단에 `limit` 확장을 유도하는 '더 보기' UI(또는 초기 limit 상향) 적용.
- **Branch:** `fix/m105-correction-status-filter` 베이스에서 `feat/m106-correction-search-expansion` 생성.

---
**STATUS:** advice_ready
**CONTROL_SEQ:** 1471
