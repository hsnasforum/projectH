# 2026-04-24 M28 Axis 3 Scoping Decision

## 개요
M28 Milestone의 세 번째 축인 "active_round selection 로직의 FSM 위임(Axis 3)" 진행 여부에 대한 검토 결과, **Option A(Axes 1+2로 M28 종료)**를 권고합니다.

## 판단 근거
1. **리스크 해소 완료**: M28의 핵심 목표는 여러 모듈에 흩어져 있던 상태 변경(write/transition) bypass를 `StateMachine`(FSM)으로 모으는 것이었습니다. Axis 1(close chain)과 Axis 2(lease release)를 통해 이 목표가 성공적으로 달성되었으며, 상태 오염의 주된 원인이 제거되었습니다.
2. **읽기 표면의 응집성**: `supervisor.py`의 `_build_active_round`는 순수하게 상태를 읽어 전시용 구조체를 만드는 "read surface"입니다. 현재 로직이 `supervisor.py` 내부에 응집되어 있고, 실질적인 상태 전이를 일으키지 않으므로 시급한 아키텍처적 결함으로 보기 어렵습니다.
3. **작업 트리 복잡도 관리**: 현재 작업 트리에는 `pipeline_runtime/cli.py`, `supervisor.py`, `operator_autonomy.py` 등에 걸쳐 이전 라운드의 미커밋 변경사항(dirty files)이 산재해 있습니다. 이 상황에서 추가적인 구조적 변경(Axis 3)을 `supervisor.py`에 주입하는 것은 검증 복잡도를 높이고 충돌 리스크를 키울 수 있습니다.
4. **효율성 우선**: `GEMINI.md` 원칙에 따라 "만약의 경우를 대비한(just-in-case)" 대안보다, 명확한 고착 상태나 모호성이 해결된 시점에서 다음 Milestone으로 전환하는 것이 전체 프로젝트 진척에 유리합니다.

## 결론
M28은 Axis 1과 2의 성공적 검증으로 "Structural Bundle" 목표를 충분히 달성했습니다. Axis 3를 생략하고 M28을 닫음으로써, 현재 산재한 dirty files의 안정화 및 다음 Milestone 방향 설정에 집중할 것을 권고합니다.

## 권고 사항
- **RECOMMEND: close M28 with Axes 1+2 and proceed to next milestone.**
- 현재 작업 트리의 `pipeline_runtime/` 계열 파일들의 진실성 동기화(truth-sync)를 다음 우선순위로 검토하십시오.
