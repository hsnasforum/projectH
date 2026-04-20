# 2026-04-20 E3 wording polish arbitration

## 변경 파일
- report/gemini/2026-04-20-e3-wording-polish-arbitration.md
- .pipeline/gemini_advice.md

## 사용 skill
- round-handoff: seq 428 arbitration 요청(`.pipeline/gemini_request.md`)에 대해 Milestone 4 Option E 후보 중 E3(wording polish)를 선택하고, `app/static/app.js`와 `core/agent_loop.py`의 구체적인 symbol과 wording 불일치를 핀하여 handoff가 즉시 작성 가능한 상태로 조언을 남깁니다.

## 변경 이유
- Milestone 4 Option E 중 E1이 seq 427에서 완료되었습니다. 남은 후보 E2(downgrade edge)와 E3(wording polish) 중, E3가 브라우저 패널(`app.js:2442`)의 "중복 지침(redundant directives)"과 "퇴보 등급 미분화(unrefined regression tiers)" 문제를 더 명확하게 해결할 수 있는 user-visible improvement 축으로 판단되었습니다.
- 특히 `app.js:2442`가 출력하는 `"추가 교차 검증이 권장됩니다"` 문구는 `curr === "단일 출처"`일 때 `:2502`에서 이미 출력되는 힌트와 중복되며, `curr === "미확인"`일 때는 "교차 검증"보다 "추가 출처 확보"가 우선이라 부적절합니다.
- 서버 측(`core/agent_loop.py:4482`)은 이미 `prev_status == STRONG`인 경우 `"교차 확인 기준을 더 이상 충족하지 않아..."`라는 더 나은 문구를 쓰고 있으나, 클라이언트와 싱크가 어긋나 있고 `WEAK → MISSING` 케이스는 여전히 제네릭한 `"약해졌습니다"`에 머물러 있어 paired refinement가 필요합니다.

## 핵심 변경 (Recommendation)
- **E3 선택**: Milestone 4 non-CONFLICT transition wording polish.
- **Client Site**: `app/static/app.js:2441-2443` 의 `buildFocusSlotExplanation` regressed 분기 수정.
  - `STRONG → WEAK`: `"→ 재조사 결과: 교차 확인 기준을 더 이상 충족하지 않아 {curr} 상태로 조정되었습니다."` (중복 지침 제거)
  - `WEAK → MISSING`: `"→ 재조사 결과: 정보를 더 이상 찾을 수 없어 {curr} 상태로 조정되었습니다."`
- **Server Site**: `core/agent_loop.py:4482-4485` 의 `_annotate_claim_coverage_progress` fallback wording 수정.
  - `prev_status == WEAK` (사실상 `WEAK → MISSING` 케이스) 시 `"정보를 더 이상 찾을 수 없어..."` 계열로 강화.
- **Regression**:
  - Playwright: `e2e/tests/web-smoke.spec.mjs:1770` (`claim-coverage panel은 재조사 후 약해진 슬롯을 명확히 표시합니다`) assertion 업데이트.
  - Smoke: `tests/test_smoke.py` 내 server-side summary string regression 추가.

## 검증
- `app/static/app.js:2441-2443` vs `core/agent_loop.py:4482-4485` 코드 대조 완료.
- `e2e/tests/web-smoke.spec.mjs:1770` 시나리오 존재 확인.
- `app.js:2502` 의 `단일 출처` 전용 힌트(`"추가 교차 검증이 권장됩니다"`)와 `:2442` 설명의 중복 확인.

## 남은 리스크
- E2(mixed support downgrade)는 여전히 Milestone 4의 "correctness" 리스크로 남아 있으나, 현재 fixture에서 관찰 가능한 edge 케이스가 명확하지 않아 synthetic regression 우려가 있습니다. E3 완료 후 E2용 fixture 보강과 함께 다음 arbitration을 여는 것을 권장합니다.
- wording 변경이므로 Playwright `-g` rerun이 필수적입니다.
