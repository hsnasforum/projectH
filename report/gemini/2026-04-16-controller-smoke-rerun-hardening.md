# 2026-04-16 controller smoke rerun hardening advisory

## 분석 및 추천
- **추천 슬라이스**: `controller smoke rerun hardening`
- **선택 이유**:
    - **Risk Reduction**: 최신 검증(@verify/...)에서 확인된 `Address already in use` 리스크를 해결하여 3-agent 운영의 재현성 및 검증 신뢰도를 확보합니다. 현재 고정 포트 `8781`과 `reuseExistingServer: false` 설정은 병렬 검증이나 빠른 재실행 시 충돌을 유발합니다.
    - **Operator Ergonomics**: 현재 `Makefile` 등에 controller 전용 테스트 진입점이 없어 operator가 매번 긴 명령어를 직접 입력해야 하는 불편함(erroneous redundancy)을 해소합니다.
    - **Tie-break Comparison**: `app.web`은 현재 'reviewed memory'의 session-aggregate 상태를 마무리하고 cross-session durable memory로 넘어가는 복잡한 설계 전환점에 있습니다. 이 시점에서 broad family를 다시 여는 것보다, 이미 truthfully closed된 controller storage family의 잔여 리스크를 surgical하게 제거하는 것이 `GEMINI.md`의 우선순위(same-family current-risk reduction)에 부합합니다.

## 상세 범위 및 제약
- **대상 파일**:
    - `e2e/playwright.controller.config.mjs`: 환경 변수(예: `CONTROLLER_SMOKE_PORT`)를 통해 포트를 유연하게 선택할 수 있도록 수정하고, `webServer` 명령어가 이를 전달하도록 개선합니다.
    - `Makefile`: `controller-test` 타겟을 추가하여 `cd e2e && npx playwright test -c playwright.controller.config.mjs` 실행을 표준화합니다.
    - `docs/ACCEPTANCE_CRITERIA.md`: 'Test Gates' 섹션에 controller 전용 smoke gate를 공식화하여 문서화합니다.
- **제약 사항**:
    - controller는 여전히 `app.web` release gate 밖의 internal/operator tooling으로 유지합니다.
    - 포트 충돌 해결을 위해 `reuseExistingServer: true`를 함부로 사용하지 않고(stale server 리스크), 포트 고립(isolation)을 우선합니다.

## 검증 전략
- **Narrowest Verification**:
    - `make controller-test` 명령어가 정상 동작하는지 확인.
    - 다른 프로세스가 `8781`을 사용 중일 때 환경 변수를 통해 다른 포트로 우회하여 테스트가 성공하는지 확인.
- **Handoff**:
    - Codex는 본 조언을 바탕으로 `.pipeline/claude_handoff.md`를 직접 작성할 수 있습니다.

## 결정 근거
- `GEMINI.md` 판단 우선순위 1번(same-family current-risk reduction)을 적용했습니다. `app.web`으로의 성급한 복귀보다 현재 family의 verification 리스크 제거가 파이프라인 운영의 truthful 진척에 더 기여합니다.
