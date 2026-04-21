# 2026-04-20 G-axis third slice prioritization

## 개요
- seq 441(G2)과 seq 444(G1)를 통해 `support_plurality`와 `trust_tier` 필드가 클라이언트 UI에 성공적으로 반영됨.
- 현재 서버 사이드 요약 헬퍼인 `_build_claim_coverage_progress_summary`는 `support_plurality`를 포커스 슬롯에 대해서만 부분적으로 소비하고 있으며, `trust_tier`는 전혀 소비하지 않고 있음.
- 다음 슬라이스로 G2-followup(서버 요약 대칭성)을 선정하여 지표 소비 사이클을 완결하고자 함.

## 판단
1. **internal cleanup/symmetry (우선순위 1):**
   - 클라이언트는 이미 "여러 출처" 및 "신뢰도 약함(mixed)" 힌트를 보여주고 있지만, 서버가 생성하는 `claim_coverage_progress_summary` 문장은 여전히 "단일 출처 상태" 또는 일반적인 "교차 확인" 문구만 내뱉고 있음.
   - 이 불일치는 사용자에게 혼란을 줄 수 있는 current-risk이며, 서버-클라이언트 간의 truth-sync를 위해 G2-followup이 가장 적절한 다음 단계임.

2. **same-family current-risk reduction (우선순위 2):**
   - 비포커스 슬롯(unresolved fallback)의 경우, 여러 출처가 발견되었음에도 "단일 출처 상태"라고 요약되는 것은 명백한 "lie"임.
   - 이를 "여러 출처 확인" 등으로 교정하는 것은 데이터 정확성 측면에서 중요함.

3. **기타 후보 검토:**
   - **G3/G4 (Tuning):** 지표 노출이 요약 문장까지 완전히 완료된 후, 실제 노출되는 텍스트의 빈도와 정확도를 보며 튜닝하는 것이 순서상 맞음.
   - **G5/G6 (Test Fix):** 전체 테스트 실패군은 여전히 별도 라운드 몫으로 유지함. 현재 기능 개선 흐름의 완결성이 더 시급함.
   - **G7/G8:** 인프라/어휘 정합성 작업은 기능적 진척 이후로 후순위 유지.

## 권고 (RECOMMEND)
- **G2-followup: non-focus multi-source/mixed-trust summary symmetry**
- 구체적 범위:
  - `core/agent_loop.py::_build_claim_coverage_progress_summary` 수정.
  - `current_trust_tier_map`을 추가하고 `unresolved_slots` 튜플을 5-tuple(`slot, label, status, plurality, trust`)로 확장.
  - 비포커스 요약(`unresolved_summary`) 생성 시, `WEAK + multiple`인 경우 `{slot} 여러 출처 확인`, `STRONG + mixed`인 경우 `{slot} 교차 확인(출처 약함)` 등으로 라벨을 스왑하여 문장에 반영.
  - 포커스 슬롯 분기에서도 `STRONG + mixed`인 경우에 대한 힌트 추가 (클라이언트 `buildFocusSlotExplanation`과 대칭).
  - `tests/test_smoke.py`의 `-k progress_summary`에 비포커스 멀티 소스 요약 검증 추가.

## 결론
G1/G2로 시작된 지표 소비 작업을 서버 요약 레이어까지 확장하여, 시스템 전체의 응답 일관성을 확보하는 것을 추천함.
