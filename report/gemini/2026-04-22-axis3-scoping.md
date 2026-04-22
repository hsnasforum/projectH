# 2026-04-22 4축 오너 번들: Axis 3 (Lease Release) 권고

## 개요
CONTROL_SEQ 747에서 Axis 2(verify close chain)가 성공적으로 완료되어 `ActiveControlSnapshot`을 기반으로 한 명시적 라운드 종료 판단이 가능해졌습니다. 이제 라운드 종료와 맞물려 실행 자원(lease)을 반납하는 과정을 정규화하고 가시성을 높이는 **Axis 3 (Lease Release)** 구현을 권고합니다.

## 후보 검토 및 판정

### 1. Axis 3: Lease Release - **권고**
- **판정**: 라운드 생명주기(Parsing -> Close -> Release)를 완성하는 논리적 후속 단계입니다.
- **이유**: 현재 `verify_fsm.py`의 `StateMachine` 내부에 10여 군데 흩어져 있는 `self.lease.release` 호출은 개별 분기마다 수동으로 관리되고 있어 누락이나 지연 리스크가 있습니다. 또한, 어떤 job이 어떤 lane의 lease를 쥐고 있는지는 `.lock` 파일을 직접 열어보지 않으면 알 수 없어 자동화 모니터링이 어렵습니다.
- **해결 과제**: 
  - `ActiveControlSnapshot`에 lease 상태(job_id, round 등)를 포함하여 전체 시스템이 lane의 점유 상태를 즉시 알 수 있게 합니다.
  - `StateMachine`의 종료 경로를 통합하여 lease 반납이 "CLOSED" 상태 전이와 원자적으로(논리적으로) 묶이도록 합니다.

### 2. Axis 4: Active Round Selection
- **판정**: 보류
- **이유**: 여러 후보 중 어떤 것을 활성 라운드로 올릴지(Selection) 결정하는 로직은, 개별 라운드의 시작과 끝(Close/Release)이 완벽하게 제어되는 상태에서 구현하는 것이 더 안전합니다. Axis 3을 통해 개별 라운드 리소스 정리가 확보된 후 진행하는 것을 추천합니다.

### 3. 제품 마일스톤 재개
- **판정**: 보류
- **이유**: "v1.5 structural" 단계의 지침(구조 안정화 우선)에 따라, 파이프라인의 기초 체력인 4축 번들을 먼저 완수해야 합니다. 인프라의 "Ordinary next-step" 자동화가 완성되지 않은 상태에서의 기능 추가는 기술 부채를 가중시킵니다.

## 권고 사항
**RECOMMEND: implement `lease_release`**

- **목표**: 흩어진 lease 반납 로직을 통합 헬퍼로 집중시키고, 공유 스냅샷(`PipelineControlSnapshot`)에 lease 점유 정보를 노출함.
- **소유 모듈**: `pipeline_runtime/schema.py`, `verify_fsm.py` (`StateMachine`), `watcher_core.py`.
- **진입점**: 
  - `pipeline_runtime/schema.py`: `ActiveControlSnapshot`에 `lease` 필드(job_id, round 등 포함) 추가.
  - `verify_fsm.py`: `self.lease.release` 호출부들을 단일 헬퍼로 통합하고, snapshot 업데이트와 연동.
  - `watcher_core.py`: `_archive_matching_verified_pending_jobs` 등에서 발생하는 예외적 lease 정리 로직 동기화.
- **기대 효과**: 리소스 점유 가시성 확보, 프로세스 크래시나 중단 후 stale lease 정리의 정확도 향상.
