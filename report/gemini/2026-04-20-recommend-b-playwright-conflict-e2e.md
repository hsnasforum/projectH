# 2026-04-20 Gemini Advisory: CONFLICT 체인 E2E 검증 추천

## 상황 분석
- seq 414를 통해 `claim_coverage`의 `CONFLICT` 상태가 서버 페이로드(`rendered_as = "conflict"`, `status_label = "정보 상충"`)부터 브라우저 포매터, 문서화까지 모두 반영되었습니다.
- 이제 `CONFLICT` 체인은 서버 방출 -> 응답 본문 헤더 -> 근거 출처 섹션 -> 요약 바 -> 패널 힌트 -> 패널 상세까지 모든 표면(surface)에 걸쳐 포화(saturated)된 상태입니다.
- 다음 단계로 Milestone 4의 여러 후보(B/C/D/E)가 있으나, 현재 가장 시급한 것은 최근 복잡하게 확장된 CONFLICT 체인이 실제 라이브 세션에서 의도대로 통합되어 작동하는지 확인하는 **리스크 감소(Risk Reduction)** 단계입니다.

## 추천 결정
- **RECOMMEND: implement Option B (Optional Playwright scenario pinning CONFLICT surfaces)**
- 이유:
  1. **리스크 감소 (Priority 1):** 서버 로직(`core/`)과 브라우저 렌더링(`app/static/`)이 복잡하게 얽힌 CONFLICT 체인의 회귀를 방지하기 위해 단일 유닛 테스트 이상의 E2E 검증이 필요합니다.
  2. **사용자 가시적 개선 확인 (Priority 2):** 응답 본문의 헤더(`상충하는 정보 [정보 상충]:`), 근거 출처(`근거 출처:`), 그리고 패널의 `"상충 정보 반영"` 문구가 실제 사용자 화면에 올바르게 배치되는지 확정합니다.
  3. **가장 명확한 슬라이스:** C/D/E는 수치적/텍스트적 경계 결정이 더 필요하지만, B는 이미 배포된 표면들을 고정(pinning)하는 것이므로 모호함이 가장 적습니다.

## 차기 슬라이스 상세 (Option B)
- **대상 파일:** `e2e/tests/web-smoke.spec.mjs` (필요시 최소한의 fixture 확장 포함)
- **범위:** 
  - 하나 이상의 `CONFLICT` 슬롯을 포함하는 엔티티 카드 조사 시나리오 추가.
  - 검증 사항:
    1. 대화창 응답 본문에 `상충하는 정보 [정보 상충]:` 헤더 포함 여부.
    2. `근거 출처:` 섹션에 상충 슬롯의 소스 URL이 CONFLICT 블록 내에 포함되는지 확인.
    3. 상세 패널의 해당 슬롯 `rendered_as` 행이 `"상충 정보 반영"` 텍스트를 렌더링하는지 확인.
- **제약:** 공유 브라우저 헬퍼(helper)를 수정하지 않고 기존 인프라 내에서 패시브 리드(passive read) 위주로 작성할 것. `core/`나 `app/static/` 코드는 수정하지 않음.

## 검증 계획
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "<new title>" --reporter=line`
- `git diff --check`
- (유닛 테스트는 seq 414에서 이미 충분히 수행됨)
