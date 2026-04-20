# 2026-04-20 G-axis (Axis Rotation) 중재 보고서

## 개요
- **상태**: Milestone 4 E2b-α 완료 후 축 전환(Axis Rotation) 단계.
- **배경**: seq 438에서 `trust_tier`와 `support_plurality` 내부 필드가 성공적으로 도입됨. seq 439 request는 G-axis의 첫 번째 슬라이스로서 여러 후보(G1~G8) 중 하나를 선택할 것을 요청함.

## 중재 판단
- **선택 슬라이스**: **G2 (Opt-in UI consumption of support_plurality + coordinated truth-sync)**
- **이유**: 
  - `current-risk reduction > same-family user-visible improvement` 원칙을 적용함.
  - G2는 현재 UI에서 `support_plurality === "multiple"`인 경우에도 "1개 출처만 확인됨"이라고 표시하는 **사실적 오류(UI Lie)**를 수정하는 리스크 감소 작업임.
  - 또한, `tests.test_web_app`에서 발생하는 wording 불일치 실패를 해결하는 truth-sync를 포함하여 "진단 소음(Diagnostic Noise)"을 줄임.
  - α 슬라이스에서 확보한 데이터를 즉시 사용자 가치로 연결하는 가장 일관성 있는 후속 조치임.

## 세부 사양 (Pinning)
1. **서버 사이드 (core/agent_loop.py)**:
   - `_build_claim_coverage_progress_summary` 내의 `unresolved_slots` 수집 루프에서 `support_plurality` 필드를 함께 추출함.
   - `cur_status == CoverageStatus.WEAK` 분기에서 `plurality == "multiple"`인 경우: `"아직 여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다."` 반환.
   - 기존 `"아직 한 가지 출처의 정보로만 확인됩니다."`는 fallback으로 유지.
2. **클라이언트 사이드 (app/static/app.js)**:
   - `renderClaimCoverage` 비포커스 힌트 분기(`statusLabel === "단일 출처"`) 수정: `item.support_plurality === "multiple"`이면 `"→ 여러 출처가 확인되었으나 교차 확인 기준에는 미달합니다."` 출력.
   - `buildFocusSlotExplanation`(`curr === "단일 출처"`) 수정: `item.support_plurality === "multiple"`이면 `"→ 재조사 대상이며 여러 출처가 확인되었으나, 아직 교차 확인 기준에는 미달합니다."` 반환.
3. **검증 방식**:
   - `tests/test_web_app.py` 내의 관련 어서션 업데이트 (G6 일부 포함).
   - `e2e/tests/web-smoke.spec.mjs`에 다수 출처 WEAK 상태를 검증하는 Playwright 시나리오 1건 추가.
   - `python3 -m unittest tests.test_smoke -k progress_summary` 및 `-k coverage` 실행.

## 향후 방향
- G2 완료 후, 남아 있는 `trust_tier == "mixed"` 소비(G1) 또는 `pipeline_gui` 테스트 실패(G5) 및 SQLite `AttributeError`(G6 본체) 해결을 다음 축으로 검토함.
