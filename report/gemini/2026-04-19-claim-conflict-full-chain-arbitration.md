# 2026-04-19 claim conflict full chain arbitration

## 개요
- **Arbitration 대상**: Seq 370 차기 slice 결정
- **결정**: Option B (`Claim Coverage Summary CONFLICT — full browser-visible chain`) 선택
- **Exact Slice**: `app/serializers.py` + `app.js` + `e2e`: full browser-visible CONFLICT counter

## 판단 근거
1. **가독성 및 Truthfulness (Same-family current-risk reduction)**: 이전 라운드들(Seq 366, 369)을 통해 core logic과 agent loop 내부에서는 `CONFLICT`가 완전히 구분되어 동작하고 있습니다. 하지만 `app/serializers.py`와 `app.js`가 업데이트되지 않아, 사용자가 보는 히스토리 카드(사실 검증 요약)에서는 여전히 `CONFLICT` 슬롯이 카운트에서 누락되거나 평탄화되어 보입니다. 이는 내부 상태와 외부 표시 사이의 불일치(Drift)를 야기하므로, 이를 한 번에 닫는 것이 가장 안전합니다.
2. **Axis 전환 전 완결성**: `GEMINI.md`의 우선순위에 따라 same-family의 user-visible improvement를 완성하는 것이 새로운 axis(Milestone 4의 다른 축)로 넘어가기 전의 논리적 순서입니다. 
3. **리스크 관리**: Option A(payload only)는 브라우저가 새 키를 무시하게 두는 "반쪽짜리" 구현이며, 결국 Option B로 가기 위한 중간 단계일 뿐입니다. 현재 프로젝트 구조상 `app.js`와 `e2e` 테스트 코드가 밀접하게 연결되어 있으므로, 이를 분리하여 여러 라운드에 걸쳐 수정하기보다는 하나의 coherent slice로 처리하여 truth-sync를 한 번에 맞추는 것이 효율적입니다.

## 추천 Slice 상세
- **Title**: `Claim Coverage Summary CONFLICT — full browser-visible chain`
- **목적**: `CONFLICT` 상태의 슬롯을 히스토리 카드의 "사실 검증" 요약 카운트에 포함하고, 브라우저 UI에서 "정보 상충" 라벨과 함께 표시되도록 전체 체인을 연결합니다.
- **범위**:
  - `app/serializers.py`: `claim_coverage_summary` dict에 `CoverageStatus.CONFLICT` 카운트 추가.
  - `app/static/app.js`: `formatClaimCoverageCountSummary` 함수에서 `conflict` 카운트를 읽어 `"정보 상충 N"` 형식으로 렌더링하도록 수정.
  - `tests/test_web_app.py`: Serializer 결과값에 `conflict` 키가 포함되는지 확인하는 focused test 추가.
  - `e2e/tests/web-smoke.spec.mjs`: `claim_coverage_summary` fixture들에 `conflict: 0` (또는 필요 시 non-zero) 필드를 추가하고, 렌더링된 텍스트 assertions 업데이트.
  - `docs/ARCHITECTURE.md` 또는 `PRODUCT_SPEC.md`: (필요 시) `CoverageStatus` 설명에 `CONFLICT` 추가.
- **검증**:
  - `python3 -m unittest tests.test_web_app` (관련 테스트)
  - `npx playwright test e2e/tests/web-smoke.spec.mjs` (관련 시나리오)
  - `python3 -m py_compile app/serializers.py`

## 리스크 및 주의사항
- `e2e` 테스트와 `test_web_app.py`에 하드코딩된 dict shape lock이 많으므로, 모든 관련 fixture를 찾아 `conflict` 키를 누락 없이 추가해야 테스트가 깨지지 않습니다.
- `app.js` 수정 시 기존 `strong`, `weak`, `missing` 렌더링 순서와 일관성을 유지해야 합니다. (교차 확인 -> 정보 상충 -> 단일 출처 -> 미확인 순서 권장)
