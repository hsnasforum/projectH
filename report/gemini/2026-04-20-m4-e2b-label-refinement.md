# 2026-04-20 Milestone 4 Option E2b arbitration

## 변경 파일
- report/gemini/2026-04-20-m4-e2b-label-refinement.md
- .pipeline/gemini_advice.md

## 사용 skill
- round-handoff: seq 431 arbitration 요청(`.pipeline/gemini_request.md`)에 대해 Milestone 4의 최종 후보인 E2b(local label refinement in `_build_entity_claim_coverage_items`)를 선택하여 권고합니다.

## 변경 이유
- Milestone 4의 다른 후보들이 소스 가중치와 재조사 캡 등을 통해 "상태(Status)"의 신뢰도를 높였다면, E2b는 그 상태를 사용자에게 "어떻게 부를 것인가(Labeling)"의 정밀도를 닫는 작업입니다.
- 특히 "단일 출처" 문구는 실제 출처가 2개 이상인 WEAK 슬롯(예: 블로그 2곳)에서 기술적으로 부정확하다는 피드백을 해소할 수 있습니다.
- "교차 확인" 문구 역시 공식 출처가 포함된 경우와 커뮤니티 합의만 있는 경우를 라벨 수준에서 분리함으로써 시스템의 근거 판단 깊이를 더 투명하게 드러낼 수 있습니다.

## 핵심 변경 (Recommendation)
- **E2b 선택**: entity-card status label plurality and trust-mix refinement.
- **Site**: `core/agent_loop.py::_build_entity_claim_coverage_items` (약 `:4272` 부근).
- **Refinement 1 (Weak Plurality)**: `status == CoverageStatus.WEAK` 이고 `candidate_count >= 2` 인 경우, `status_label`을 `"다수 출처"`로 변경.
- **Refinement 2 (Strong Authority Downgrade)**: `status == CoverageStatus.STRONG` 이더라도, `primary_claim.supporting_sources` 중 `OFFICIAL`이나 `DATABASE` 역할이 전무한 경우 `status_label`을 `"다수 출처 합의"`로 변경.
- **Regression**: `tests/test_smoke.py` 내 `test_build_entity_claim_coverage_items_label_refinement` 추가. 

## 검증
- `core/agent_loop.py` 내 metadata 가용성 확인 (이미 `slot_coverage`와 `primary_claim`에 접근 가능).
- `app/static/app.js`는 서버가 준 `status_label`을 그대로 사용하므로 프런트엔드 수정 불필요.
- 기존 Playwright fixtures 중 `candidate_count >= 2`인 WEAK 슬롯이 있는 경우 assertion 업데이트 필요 여부 대조.

## 남은 리스크
- Milestone 4의 마지막 slice로서, 이 작업 이후에는 Milestone 5(Grounded Brief Contract)로의 축 전환(Option G)을 권고합니다.
- 라벨 문자열 변경으로 인해 Playwright smoke 시나리오 중 일부에서 assertion flip이 발생할 수 있으므로, isolated rerun 검증이 필수적입니다.
