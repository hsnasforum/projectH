# 2026-04-22 4축 오너 번들: Axis 2 (Verify Close Chain) 권고

## 개요
CONTROL_SEQ 742에서 Axis 1(공유 상태 파싱)이 성공적으로 완료되어 `ActiveControlSnapshot`이라는 강력한 통합 데이터 모델이 확보되었습니다. 다음 단계로 이 스냅샷을 활용하여 라운드 종료 판단 로직을 정규화하는 **Axis 2 (Verify Close Chain)** 구현을 권고합니다.

## 후보 검토 및 판정

### 1. Axis 2: Verify Close Chain - **권고**
- **판정**: 가장 시급한 구조적 개선 사항입니다.
- **이유**: 현재 `verify_fsm.py`의 `StateMachine`은 라운드 종료(implement round의 완료 및 verify round의 진입/종료)를 감지할 때 `.pipeline/` 폴더 내 여러 파일의 시그니처가 바뀌었는지를 체크하는 "fuzzy"한 방식(`compute_multi_file_sig`)에 의존하고 있습니다. 이는 우연한 파일 수정이나 시그니처 충돌에 취약합니다.
- **해결 과제**: Axis 1에서 확보한 `ActiveControlSnapshot`을 사용하여, 검증자가 자신이 맡은 특정 `CONTROL_SEQ`가 영수증(receipt)에 의해 닫혔거나 새로운 제어 신호에 의해 대체되었음을 "정확하게" 판단하도록 전환해야 합니다.

### 2. Axis 3/4 (Lease Release / Active Round Selection)
- **판정**: 보류
- **이유**: Axis 4는 Axis 1에 의해 이미 기반이 닦여 있으며, Axis 2가 완료되어 라운드 생명주기가 명확해진 후에 선택 로직을 강화하는 것이 더 자연스럽습니다. Axis 3은 운영 편의에 가까워 구조적 리스크 감소 우선순위에서 밀립니다.

### 3. 제품 마일스톤 재개
- **판정**: 보류
- **이유**: "v1.5 structural" 단계의 지침인 "기능 추가 보류, 구조 안정화 우선"을 유지해야 합니다. 파이프라인 자동화의 핵심인 라운드 체이닝(Chain)이 아직 시그니처 기반의 불안정한 상태이므로, 이를 먼저 해결하는 것이 "Ordinary next-step에서 operator를 부르지 않는다"는 목표에 부합합니다.

## 권고 사항
**RECOMMEND: implement `verify_close_chain`**

- **목표**: `StateMachine` (및 관련 watcher 로직)에서 시그니처 기반 종료 감지(`feedback_baseline_sig`)를 제거하고, `ActiveControlSnapshot` 기반의 명시적 라운드 종료 감지로 전환.
- **소유 모듈**: `verify_fsm.py` (`StateMachine`), `pipeline_runtime/supervisor.py`.
- **진입점**: 
  - `verify_fsm.py`: `_handle_verify_running` (L520 부근) - 시그니처 비교 로직을 스냅샷 비교로 대체.
  - `pipeline_runtime/supervisor.py`: `_reconcile_receipts` (L1574 부근) - 영수증 작성이 런타임 상태에 "CLOSED"로 정확히 반영되도록 보장.
- **기대 효과**: 라운드 전이의 정밀도 향상, 상태 불일치로 인한 무한 루프 또는 오작동 리스크 감소.
