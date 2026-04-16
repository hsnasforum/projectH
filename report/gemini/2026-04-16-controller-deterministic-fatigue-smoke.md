# 2026-04-16 controller deterministic fatigue smoke

## 상황 요약
- `work/4/16/2026-04-16-controller-office-agent-movement-fatigue-polish.md` 라운드에서 controller 사이드바에 agent fatigue observability(`data-fatigue`, `.agent-fatigue`)가 추가되었습니다.
- `verify/4/16/2026-04-16-controller-smoke-rerun-hardening-verification.md` 라운드에서 `make controller-test` 재실행을 시도했으나, 샌드박스 환경의 소켓 생성 제한(`PermissionError: [Errno 1]`)으로 인해 런타임 검증을 truthfully 완료하지 못했습니다.
- 현재 controller fatigue 기능은 15초의 하드코딩된 임계값에 의존하고 있어, smoke 테스트가 실시간 대기에 의존하는 "brittle long wait" 리스크를 안고 있습니다.

## 후보 비교 및 판단
- **후보 A: Deterministic fatigue transition smoke via state-injection (추천)**
  - **이유**: `GEMINI.md`의 우선순위 1번인 "same-family current-risk reduction"에 해당합니다. 15초 대기에 의존하는 테스트는 불안정하며, 특히 현재처럼 실행 환경이 제한적인 경우 테스트 효율성을 극도로 저하시킵니다. `window` API 등을 통해 상태를 강제 주입하여 `fatigued` 및 `coffee` 상태 전환을 즉각 검증하는 구조를 갖추는 것이 가장 시급한 리스크 감소 조치입니다.
- **후보 B: Drone Delivery / Monitor Matrix observability 추가**
  - **이유**: "same-family user-visible improvement"에 해당하나, 아직 fatigue 시스템의 테스트 안정성이 확보되지 않은 상태에서 새로운 가시적 기능을 추가하는 것은 기술적 부채를 늘리는 방향입니다.
- **후보 C: `app.web` axis 복귀**
  - **이유**: "new quality axis" 전환에 해당하나, 현재 controller family의 fatigue slice가 "검증 불안정성"이라는 명확한 잔류 리스크를 남긴 채 닫히는 것은 truth-sync 관점에서 부적절합니다.

## 권고 사항 (RECOMMEND)
- **명칭**: `implement deterministic controller fatigue transition smoke via state-injection`
- **전략**: `controller/index.html`에 테스트용 상태 주입 API(예: `window.setAgentFatigue`)를 노출하고, `e2e/tests/controller-smoke.spec.mjs`에서 이를 호출하여 15초 대기 없이 `fatigued`와 `coffee` 상태의 UI 반영을 즉각 검증합니다.
- **범위**:
  - `controller/index.html`: `window` 전역 객체에 특정 agent의 fatigue 수치를 조정할 수 있는 헬퍼 함수 추가.
  - `e2e/tests/controller-smoke.spec.mjs`: 새 시나리오 추가 (`should show fatigue indicator immediately when state is injected`).
  - `docs/ACCEPTANCE_CRITERIA.md`: controller smoke의 결정론적 전이 검증 항목 추가.
- **검증**: `make controller-test` (환경 제약이 풀린 상태에서 통과 확인 필요).
- **Codex Action**: 이 권고를 바탕으로 `.pipeline/claude_handoff.md`를 직접 작성하여 Claude에게 구현을 위임할 수 있습니다.
