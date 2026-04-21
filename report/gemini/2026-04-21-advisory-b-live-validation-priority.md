# 2026-04-21 seq 625 menu-choice advisory arbitration: live validation priority

## 개요
- **REQUEST**: seq 625 선택지형 operator stop (`B/C/D`)에 대한 advisory-first arbitration 요청.
- **QUESTION**: (B) 라이브 런타임 검증, (C) 커밋/푸시, (D) Milestone 5 전환 중 하나를 선택.
- **DECISION**: **RECOMMEND: implement live runtime G4 DISPATCH_SEEN + idle-release validation (Choice B)**

## 판단 근거
1. **기술적 완결성**: `feat/watcher-turn-state` 브랜치의 모든 계획된 구현(G4~G15) 및 주석 동기화가 완료되었습니다. 단위 테스트(Watcher 154, Supervisor 111)가 모두 통과(Code-Green) 상태입니다.
2. **최종 기술 게이트**: 브랜치 종료(C) 및 다음 마일스톤 진입(D) 전, `_write_task_hints`에 의한 synthetic ID 주입 및 `idle-release` 로직이 실제 통합 환경에서 의도대로 작동하는지(`events.jsonl` 확인) 검증하는 것이 가장 시급하고 논리적인 단계입니다.
3. **Verify-First 원칙**: `B/C/D`는 병렬 선택지가 아닌 순차적 파이프라인입니다. (B) 검증 통과가 (C)와 (D)의 전제 조건이므로, 검증 레인이 즉시 실행할 수 있는 가장 구체적인 "next slice"입니다.
4. **분류기 예외 보강 필요성 확인**: 현재 `B/C/D` 메뉴가 `slice_ambiguity`로 분류된 것은 `gate_24h` 윈도우 내에서 에이전트가 먼저 판단할 기회를 준 것입니다. Gemini는 이를 "기술적 검증 우선"으로 확정하여 operator stop 없이 진척을 유도합니다.

## 권고 사항
- **NEXT ACTION**: `(B) pipeline runtime 재시작 및 G4 DISPATCH_SEEN + idle-release 검증 실행 승인`을 차기 슬라이스로 확정합니다.
- **검증 포인트**:
    - 런타임 재시작 후 `DISPATCH_SEEN` 이벤트가 synthetic ID(`ctrl-{seq}|seq-{seq}`)를 포함하여 정상 방출되는지 확인.
    - `idle-release` 조건(handoff_seq > current_seq + idle) 충족 시 `claude_handoff_idle_release` 신호가 발생하는지 확인.
- **리스크 대응**: `_MENU_CHOICE_BLOCKER_MARKERS`에 `branch/commit/push/milestone` 계열 마커를 추가하여, 향후 순수 승인 게이트가 `slice_ambiguity`로 오분류되는 false-positive를 방지할 것을 권고합니다. (이번 라운드 검증 종료 후 또는 Milestone 5 진입 시 수행)

## 결론
현재 상태에서 추가 구현 없이 (B) 검증 슬라이스를 닫고 브랜치 마무리 준비를 마치는 것이 가장 truthful한 진행 방향입니다.
