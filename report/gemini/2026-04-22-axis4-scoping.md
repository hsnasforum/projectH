# 2026-04-22 4축 오너 번들: Axis 4 (Active Round Selection) 권고

## 개요
CONTROL_SEQ 750에서 Axis 3(lease release)까지 성공적으로 완료되어 파이프라인의 기초 생명주기(Parsing -> Close -> Release)가 구조적으로 안정화되었습니다. 이제 이 기반 위에서 여러 작업(job) 중 현재 시스템이 집중해야 할 대상을 명확히 판별하고 정렬하는 **Axis 4 (Active Round Selection)** 구현을 권고합니다.

## 후보 검토 및 판정

### 1. Axis 4: Active Round Selection - **권고**
- **판정**: 4축 번들의 마지막 퍼즐이자, UI와 오토노미(autonomy) 판단의 신뢰도를 결정짓는 핵심 단계입니다.
- **이유**: 현재 `supervisor.py`의 `_build_active_round`는 `liveness_rank`와 타임스탬프 기반의 tie-break 로직을 사용하고 있지만, 이는 `PipelineControlSnapshot`이나 `ActiveControlSnapshot`과 완전히 동기화되어 있지 않습니다. 제어 신호(Control Seq)와 실제 작업 상태(Job State)가 일치하는 "진정한 활성 라운드"를 선별하는 로직을 정규화해야 합니다.
- **해결 과제**:
  - `ActiveControlSnapshot`의 `control_seq`와 일치하는 job을 최우선으로 선택하도록 `_build_active_round` 개선.
  - `suppress_active_round_for_turn` 로직을 `WatcherTurnState`와 통합하여, 특정 턴(예: ADVISORY, OPERATOR_WAIT)에서 불필요한 라운드 정보 노출 억제.

### 2. 제품 마일스톤 재개
- **판정**: 보류
- **이유**: 4축 번들이 거의 완성되었으므로, 마지막 한 단계를 마저 닫아 인프라 부채를 완전히 정리하는 것이 장기적으로 유리합니다. 인프라의 "Ordinary next-step"이 완전히 견고해진 상태에서 Milestone 5/6로 복귀하는 것이 작업 효율이 높습니다.

## 권고 사항
**RECOMMEND: implement `active_round_selection`**

- **목표**: 제어 스냅샷과 작업 상태를 결합하여 "현재 유효한 활성 라운드"를 선별하는 로직을 정규화하고, 턴 상태에 따른 표시 억제 로직 통합.
- **소유 모듈**: `pipeline_runtime/supervisor.py`, `pipeline_runtime/turn_arbitration.py`.
- **진입점**:
  - `pipeline_runtime/supervisor.py`: `_build_active_round` (L895 부근) - `ActiveControlSnapshot` 정보를 인자로 받아 selection 우선순위에 반영.
  - `pipeline_runtime/turn_arbitration.py`: `suppress_active_round_for_turn` 로직을 `WatcherTurnState` enum 기반으로 정규화.
- **기대 효과**: UI 표시와 실제 런타임 제어 상태 간의 100% 일치 보장, stale한 작업 정보로 인한 사용자/에이전트 혼란 방지.
