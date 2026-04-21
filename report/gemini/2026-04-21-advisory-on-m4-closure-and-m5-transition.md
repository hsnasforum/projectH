# 2026-04-21 feat/watcher-turn-state 브랜치 통합 및 Milestone 4 종결 권고

## 개요
CONTROL_SEQ 646 기반의 arbitration 요청에 대해, `feat/watcher-turn-state` 브랜치의 모든 구현/검증 축(G4~G15)이 완료되었음을 확인하고, 대규모 dirty worktree의 안정화를 위한 **결정 C (커밋/푸시)** 우선 처리를 권고합니다.

## 분석 결과

### 1. 구현 및 검증 상태 (Milestone 4 핵심 축 완료)
- **G4~G15 전수 완료**: signal_mismatch guard, task hint, legacy alias 제거, FSM fallback, automation health 등 모든 계획된 축이 구현 및 검증(code-green)되었습니다.
- **테스트 정합성**: Supervisor(119), Watcher(160) 등 모든 테스트 스위트가 통과하였으며, 누적된 9회 이상의 scope violation 항목들도 기능적 정합성이 확인되었습니다.
- **실환경 검증 완료**: `events.jsonl` live 집계 및 G6 환경 베이스라인(ENV_BASELINE_ONLY) 종결이 verify-lane에 의해 확인되었습니다.

### 2. 잔여 리스크 및 중단 지점
- **대규모 dirty worktree**: 현재 9회 이상의 scope violation이 누적된 상태로, 추가 구현(예: retriage age persistence)은 베이스라인 정합성 리스크를 높일 수 있습니다.
- **Operator Gate (C, D, E)**: 현재 런타임은 `gate_24h` 정책에 의해 중단되어 있으며, 이는 정책적(커밋 권한) 및 시간적(6h soak) 제약에 기인합니다.
- **Retriage Loop 해소**: seq 645 작업을 통해 semantic fingerprint 기반의 retriage loop가 기술적으로 해소되었으므로, 현재의 중단 상태는 "안정적인 대기"입니다.

## 권고 사항 (Arbitration Decision)

Gemini는 다음과 같은 이유로 **결정 C**를 최우선으로 권고합니다.

1. **안정적 베이스라인 확보 (Risk Reduction)**: 추가 기능 개발이나 soak 테스트를 진행하기 전, 이미 검증된 대규모 변경분(G4~G15)을 브랜치에 커밋하여 "Dirty Worktree"를 해소하는 것이 가장 중요합니다.
2. **PR 준비 단계 진입**: 결정 C(커밋)가 완료되어야 결정 D(6h soak)를 통해 최종 PR 오픈을 위한 에비던스를 확보할 수 있습니다.
3. **Milestone 5 전환**: Milestone 4의 기술적 부채(미커밋 변경분)를 완전히 닫아야 Milestone 5(Grounded Brief Contract)의 첫 슬라이스를 깨끗하게 시작할 수 있습니다.

## RECOMMENDATION

**RECOMMEND: needs_operator (C) feat/watcher-turn-state branch commit/push**

- 모든 구현/검증(G4-G15)이 완료되어 추가적인 자동 구현 슬라이스가 불필요합니다.
- 대규모 dirty worktree 안정화를 위해 오퍼레이터의 커밋 승인이 유일한 병목입니다.
- 커밋 후 6h soak(D) 및 Milestone 5(E)로 순차 전환할 것을 제안합니다.
