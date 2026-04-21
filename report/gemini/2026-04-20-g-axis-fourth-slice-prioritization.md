# 2026-04-20 G-axis fourth slice prioritization

## 개요
- seq 447(G2-followup narrowed)에서 포커스 슬롯의 STRONG+mixed-trust 및 비포커스 슬롯의 WEAK+multi-source 요약이 반영됨.
- 하지만 비포커스 슬롯이 STRONG이면서 mixed-trust인 경우(교차 확인은 되었으나 신뢰도 소스가 약함)는 여전히 요약 문장에서 생략되고 있음.
- 이를 해결하기 위한 G2-deferred-A 슬라이스를 선정하고, 구현 방식(shape)을 확정하고자 함.

## 판단
1. **same-family current-risk reduction (우선순위 1):**
   - 현재 비포커스 STRONG+mixed-trust 슬롯은 `unresolved_slots`에 포함되지 않아 요약 문장에서 아예 사라짐. 이는 교차 확인은 되었으나 근거가 약하다는 중요한 "품질 정보"를 누락하는 것임.
   - G2-deferred-A를 통해 이 누락을 메움으로써 서버 요약의 정직성(truthfulness)을 완성할 수 있음.

2. **구현 방식 결정 (Option i: New Collection):**
   - **Option (ii) widened unresolved_slots:** "unresolved"의 의미를 "품질 미달"까지 확장하는 것은 기존 `CoverageStatus` 중심의 로직(MISSING/CONFLICT/WEAK)과 충돌할 위험이 있음.
   - **Option (i) new `mixed_trust_slots` collection (권고):** 기존 `unresolved_slots` 루프 내에서 `current_status == STRONG` AND `trust_tier == "mixed"`인 경우를 별도 컬렉션으로 수집하는 방식.
   - 이 방식은 기존 "미결(unresolved)" 슬롯과 "품질 주의(mixed-trust)" 슬롯을 명확히 구분하면서도, 요약 문장(`unresolved_summary`)을 생성할 때 두 컬렉션을 합쳐서 처리할 수 있어 유연함.

3. **기타 후보 검토:**
   - **G2-deferred-B (Focus-steady):** 포커스 슬롯이 변화 없이 STRONG+mixed-trust인 경우는 상대적으로 발생 빈도가 낮고, 이미 개별 슬롯 라인(UI)에서 정보를 제공하고 있으므로 요약 문장 우선순위에서는 밀림.
   - **G3..G8:** 기능적 완결성(Symmetry)을 먼저 확보한 후 튜닝이나 인프라 개선으로 넘어가는 것이 안정적임.

## 권고 (RECOMMEND)
- **G2-deferred-A: STRONG non-focus mixed-trust surfacing in summary**
- 구체적 범위:
  - `core/agent_loop.py::_build_claim_coverage_progress_summary` 수정.
  - `mixed_trust_slots: list[tuple[str, str, str, str, str]]` 신규 컬렉션 도입 (루프 내 `STRONG + mixed`인 경우 append).
  - `_claim_coverage_non_focus_summary_label` 헬퍼에 `trust_tier` 인자 추가.
  - `status == STRONG and trust == "mixed"`일 때 `"교차 확인(출처 약함)"` 반환 로직 추가.
  - 비포커스 요약 생성 시 `unresolved_slots`와 `mixed_trust_slots`를 합쳐서(ordered) 상위 2-3개를 노출.
  - `tests/test_smoke.py`에 비포커스 STRONG+mixed-trust 슬롯이 요약에 포함되는지 검증하는 회귀 추가.

## 결론
G2-deferred-A를 Option (i) 방식으로 구현하여, 서버 요약 레이어에서 누락된 품질 신호를 정직하게 노출하는 사이클을 완결하는 것을 추천함.
