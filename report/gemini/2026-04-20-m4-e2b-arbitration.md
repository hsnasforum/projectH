# 2026-04-20 Milestone 4 Option E2b arbitration

## 변경 파일
- report/gemini/2026-04-20-m4-e2b-arbitration.md
- .pipeline/gemini_advice.md

## 사용 skill
- round-handoff: seq 431 arbitration 요청(`.pipeline/gemini_request.md`)에 대해 Milestone 4의 마지막 후보인 E2(strong-badge downgrade edge)를 구체적인 E2b(local override in `_build_entity_claim_coverage_items`)로 좁혀 권고합니다.

## 변경 이유
- Milestone 4(Secondary-Mode Investigation Hardening)는 오늘 소스 역할 가중치(seq 420), 재조사 캡(seq 423), 정렬 키(seq 427), regressed wording(seq 430)을 거치며 완성도에 도달했습니다.
- 마지막 남은 E2 후보는 "교차 확인" 라벨의 엄격성을 높이고, "단일 출처" 라벨의 오해(2개 이상의 출처가 있으나 신뢰도 미달인 경우)를 해소하는 데 직접적인 가치가 있습니다.
- 특히 `_claim_coverage_status_label`의 시그니처를 바꾸는 E2a보다, 이미 풍부한 metadata를 가진 `_build_entity_claim_coverage_items`에서 로컬하게 라벨을 결정하는 E2b가 "bounded helper change" 원칙에 더 잘 부합합니다.

## 핵심 변경 (Recommendation)
- **E2b 선택**: entity-card status label plurality and trust-mix refinement.
- **Site**: `core/agent_loop.py:_build_entity_claim_coverage_items` (약 `:4272` 부근).
- **Refinement 1 (Weak Plurality)**: `status == CoverageStatus.WEAK` 이고 `candidate_count >= 2` 인 경우, 기존의 오해 소지가 있는 `"단일 출처"` 대신 `"다수 출처"` 라벨을 사용합니다.
- **Refinement 2 (Strong Authority Downgrade)**: `status == CoverageStatus.STRONG` 이더라도, primary claim의 `supporting_sources` 중 `OFFICIAL`이나 `DATABASE` 역할이 하나도 포함되지 않은 경우(예: 2 Wiki sources), 권위적인 `"교차 확인"` 대신 `"다수 출처 합의"` 라벨을 사용하여 신뢰도 깊이를 차별화합니다.
- **Regression**: `tests/test_smoke.py` 내 `test_build_entity_claim_coverage_items_label_refinement` (가칭) 추가. Mocked `SlotCoverage`와 `ClaimRecord`를 사용하여 위 두 가지 라벨 분기를 검증합니다.

## 검증
- `core/agent_loop.py` 내 `_build_entity_claim_coverage_items` 시그니처와 metadata 가용성 확인 완료.
- `app/static/app.js`의 `status_label` 소비 방식 대조 완료 (서버 문자열을 그대로 노출).
- Playwright mocked fixtures와의 영향도 평가 완료 (mocked payload는 영향을 받지 않음).

## 남은 리스크
- 이번 라운드가 Milestone 4의 마지막 구현 슬라이스가 될 가능성이 큽니다. 이후에는 Milestone 5(Grounded Brief Contract)로의 축 전환(Option G)을 준비하는 것이 좋습니다.
- Playwright smoke 중 실제 backend reload/investigation을 타는 시나리오가 있는 경우, 바뀐 라벨 문자열에 맞춰 assertion 업데이트가 필요할 수 있습니다. (현재로서는 mocked payload 위주인 것으로 확인됨).
