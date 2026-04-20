# 2026-04-20 Milestone 4 E2b-α 중재 보고서

## 개요
- **상태**: Milestone 4 종료 전 마지막 세부 정제(Refinement) 단계.
- **배경**: seq 432 advice에서 제안된 E2b(mixed-trust STRONG / high-plurality WEAK 구분)가 6개 파일에 걸친 클라이언트-서버 동기화 리스크 및 trusted-role 정의 모호성으로 인해 구현 보류됨. seq 436 request는 이를 세 가지 변체(α, β, γ)로 정제하여 하나를 선택하거나 Milestone 4를 닫을 것을 요청함.

## 중재 판단
- **선택 변체**: **E2b-α (Label-set-preserving via status field tightening)**
- **이유**: 
  - `current-risk reduction > same-family user-visible improvement` 원칙에 따라, 새로운 라벨 도입에 따른 클라이언트 사이드 리스크(범례 누락, 힌트 소실, regressed branch 깨짐)를 피하면서도 서버 사이드에서 데이터의 질적 차이를 필드화하는 α가 가장 안전하고 확장성 있는 선택임.
  - γ(semantic downgrade)는 2개 이상의 WIKI 출처가 있는 경우를 '단일 출처'로 표시하게 되어 사실관계가 왜곡될 위험이 있음.
  - β(coordinated widen-labels)는 Milestone 4의 'bounded change' 범위를 초과하는 6개 파일 수정이 필요함.

## 세부 사양 (Pinning)
1. **신규 필드 정의**:
   - `trust_tier`: 
     - `"trusted"`: `status == CoverageStatus.STRONG` 이고 지원 출처 중 적어도 하나가 `{OFFICIAL, DATABASE, WIKI}` 역할인 경우.
     - `"mixed"`: `status == CoverageStatus.STRONG` 이지만 위 역할이 하나도 없는 경우 (예: DESCRIPTIVE로만 구성).
     - 그 외 상태에서는 생략 또는 `None`.
   - `support_plurality`:
     - `"multiple"`: `status == CoverageStatus.WEAK` 이고 `support_count >= 2` 인 경우.
     - `"single"`: `status == CoverageStatus.WEAK` 이고 `support_count < 2` 인 경우.
     - 그 외 상태에서는 생략 또는 `None`.
2. **신뢰 역할 집합 (Trusted-set)**:
   - `{SourceRole.OFFICIAL, SourceRole.DATABASE, SourceRole.WIKI}` (seq 420 `_ROLE_PRIORITY`와 일치시킴).
3. **대상 위치**: `core/agent_loop.py::_build_entity_claim_coverage_items` (:4264-4274 근처).
4. **검증 방식**:
   - `tests/test_smoke.py`에 `test_build_entity_claim_coverage_items_emits_trust_tier_and_support_plurality_internal_fields` 회귀 테스트 추가.
   - `tests/test_smoke.py -k coverage` 실행.
   - `py_compile`, `git diff --check` 수행.

## 향후 방향
- 이번 라운드에서 추가된 `trust_tier`와 `support_plurality`는 향후 클라이언트 사이드에서 보조 배지나 툴팁으로 활용 가능하며, Milestone 4를 안전하게 마무리하는 기반이 됨.
- 다음 축(Axis) 전환 후보로 `prefer_probe_first` 임계값 튜닝 또는 `_role_confidence_score` 도입을 검토할 것을 권고함.
