# 2026-04-20 Milestone 4 Option E2b label refinement arbitration

## 변경 파일
- report/gemini/2026-04-20-m4-e2b-label-refinement-arbitration.md
- .pipeline/gemini_advice.md

## 사용 skill
- round-handoff: seq 431 arbitration 요청(`.pipeline/gemini_request.md`)에 대해 Milestone 4의 마지막 구현 후보인 E2b(local label refinement)를 선택하여 권고합니다.

## 변경 이유
- Milestone 4의 이전 슬라이스들이 내부 로직(가중치, 캡, 정렬 키)을 다듬었다면, E2b는 그 결과를 사용자에게 전달하는 "라벨링"의 정확도를 닫는 작업입니다.
- "단일 출처" 문구는 실제 출처가 2개 이상인 WEAK 슬롯에서 명백한 오해를 불러일으키고 있으며, 이를 `"다수 출처"`로 정정하는 것은 시스템의 신뢰도에 기여합니다.
- "교차 확인" 문구 역시 공식/데이터베이스 출처 포함 여부에 따라 `"다중 출처 합의"`와 분리함으로써, 시스템이 판단하는 근거의 질적 차이를 투명하게 노출할 수 있습니다.

## 핵심 변경 (Recommendation)
- **E2b 선택**: entity-card status label plurality and trust-mix refinement.
- **Site**: `core/agent_loop.py::_build_entity_claim_coverage_items` (약 `:4272` 부근).
- **Refinement 1 (Weak Plurality)**: `status == CoverageStatus.WEAK` 이고 `candidate_count >= 2` 인 경우, `status_label`을 `"다수 출처"`로 변경.
- **Refinement 2 (Strong Authority Downgrade)**: `status == CoverageStatus.STRONG` 이더라도 `supporting_sources` 중 `OFFICIAL`/`DATABASE` 역할이 없는 경우 `status_label`을 `"다중 출처 합의"`로 변경.
- **Client Sync**: `app/static/app.js:2502` 부근에 `"다수 출처"` 전용 힌트(`"→ 다수 출처가 있으나 신뢰도가 낮음. 교차 검증이 권장됩니다."`) 추가.
- **Regression**: `tests/test_smoke.py` 내 `test_build_entity_claim_coverage_items_label_refinement` 추가 및 Playwright regressed scenario assertion 업데이트.

## 검증
- `core/agent_loop.py` 내 metadata 접근성 확인 (루프 내 `slot_coverage`와 `primary_claim` 활용).
- `app/static/app.js` 내 `status_label` 기반 조건부 렌더링 구조 대조 완료.
- Milestone 4의 "Secondary-Mode" 테두리 안에서 가장 bounded된 고부가가치 슬라이스임을 확인.

## 남은 리스크
- 라벨 문자열이 바뀌므로, Playwright smoke 테스트 중 실제 백엔드 연동을 거치는 시나리오에서 assertion flip이 발생할 수 있습니다. (E3와 마찬가지로 isolated rerun 필수).
- E2b 완료 후에는 Milestone 4를 종료하고 Milestone 5(Grounded Brief)로 전환하는 것이 적절합니다.
