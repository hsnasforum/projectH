# 2026-04-20 G-axis second slice prioritization

## 개요
- seq 441에서 G-axis의 첫 번째 슬라이스인 G2(`support_plurality` UI 소비)가 성공적으로 완료됨.
- 현재 G1(trust_tier 소비), G3/G4(Tuning), G5/G6(Test Fix), G7(Vocabulary), G8(Memory) 등 다양한 후보 간의 우선순위 모호성으로 인해 Gemini arbitration 요청됨.

## 판단
1. **same-family current-risk reduction (우선순위 1):**
   - seq 438에서 서버 사이드에 `trust_tier`와 `support_plurality`가 함께 도입되었으나, G2에서는 `support_plurality`만 UI에 연결됨.
   - `trust_tier`가 서버 메모리에는 존재하지만 클라이언트로 전달되지 않고 UI에서도 "어두운 상태"로 남은 것은 명백한 mismatch risk임.
   - G1을 수행함으로써 seq 438/441에서 시작된 "Claim Coverage 지표 고도화"의 UI 수용 사이클을 완결할 수 있음.

2. **same-family user-visible improvement (우선순위 2):**
   - 신뢰도 등급(Trusted/Standard/Low)을 UI에 표시하는 것은 사용자에게 직접적인 가치를 제공하며, G3/G4와 같은 내부 튜닝보다 체감 효과가 큼.

3. **기타 후보 검토:**
   - **G3/G4 (Float tuning):** UI 표시가 확정된 후, 실제 노출되는 지표를 보면서 튜닝하는 편이 더 안정적임.
   - **G5/G6 (Red tests):** `tests.test_web_app` 전체 실패군은 중요하지만, 현재 진행 중인 Claim Coverage 기능 개선 흐름을 끊고 전환할 만큼의 차단 요소(blocker)는 아님. `/verify`에서도 이를 별도 라운드 몫으로 정의함.
   - **G7/G8:** 내부 인프라/어휘 정합성 작업으로 현재 기능적 진척보다 우선순위가 낮음.

## 권고 (RECOMMEND)
- **G1: Opt-in UI consumption of `trust_tier`**
- 구체적 범위:
  - `app/serializers.py`에서 `trust_tier` 필드 직렬화 추가.
  - `app/static/app.js`의 `buildFocusSlotExplanation` 및 `renderClaimCoverage`에서 `trust_tier` 값(e.g., "trusted", "low")에 따른 시각적 힌트(chip, 색상, 또는 텍스트) 추가.
  - `tests/test_smoke.py` 및 `e2e/tests/web-smoke.spec.mjs`에 `trust_tier` 노출 여부 검증 추가.

## 결론
G2의 성공적인 마무리를 이어받아 G1을 수행함으로써, Claim Coverage 패널의 데이터 정밀도와 UI 표현력 사이의 간극을 완전히 닫는 것을 추천함.
