# 2026-04-22 인프라 정리 후속 슬라이스 권고

## 개요
CONTROL_SEQ 736~739를 통해 진행된 파이프라인 인프라 정리(가칭 'role-based control cleanup')가 성공적으로 완료되었습니다. 레거시 파일 제거, 제어 슬롯 레지스트리 도입, 내부 시그니처 변수 정규화가 완료되어 다음 단계로 넘어갈 준비가 되었습니다. 현재 프로젝트는 'v1.5 structural' 단계로, 기능 추가보다는 구조적 안정화와 자동화 완성도 제고에 우선순위를 두고 있습니다.

## 후보 검토 및 판정

### 1. 4축 owner bundle (shared state parsing / verify close chain / lease release / active_round selection) - **권고**
- **판정**: 현재 브랜치(`feat/watcher-turn-state`)의 핵심 목표이자 구조적 개선의 핵심입니다.
- **첫 슬라이스 선택**: `shared state parsing`
- **이유**: 나머지 3개 축(선택, 종료, 리스) 모두가 파이프라인의 전체 상태를 일관되게 읽는 데이터 레이어에 의존합니다. 현재는 watcher와 supervisor가 각자의 방식으로 슬롯을 해석하고 있어 데이터 드리프트 리스크가 있습니다. `ControlSlotSpec` 레지스트리를 확장하여 파이프라인의 전체 스냅샷을 제공하는 공유 파서를 구현하는 것이 가장 기초적인 리스크 감소 작업입니다.

### 2. lane_surface.py 어댑터 이름 cleanup
- **판정**: 보류
- **이유**: 단순 내부 정리(internal cleanup) 우선순위 4단계에 해당하며, 시스템 운영 안정성에 직접적인 영향을 주는 4축 번들에 비해 가치가 낮습니다.

### 3. 제품 마일스톤 재개 (Milestone 5/6)
- **판정**: 보류
- **이유**: 현재 'structural v1.5' 단계의 "기능 추가 보류" 지침과 충돌합니다. 파이프라인 자동화가 "ordinary next-step, ambiguity에서 operator를 부르지 않는" 수준으로 고도화되는 것이 먼저입니다.

### 4. needs_operator
- **판정**: 불필요
- **이유**: 단순 방향 선택의 문제이며, 기존 가이드라인(구조 우선, 리스크 감소 우선)에 따라 충분히 에이전트 간 협의로 결정 가능한 범위입니다.

## 권고 사항
**RECOMMEND: implement `shared state parsing`**

- **목표**: `pipeline_runtime/schema.py`의 `ControlSlotSpec`을 기반으로, 전체 `.pipeline/` 디렉터리의 상태(시퀀스, 시그니처, 활성 슬롯 등)를 하나의 일관된 데이터 구조로 제공하는 공유 상태 파서 구현.
- **기대 효과**: watcher_core와 supervisor 간의 상태 인식 불일치 제거, 후속 `active_round selection` 및 `lease release` 구현을 위한 신뢰할 수 있는 기반 마련.
- **위치**: `pipeline_runtime/` 폴더 내 (예: `pipeline_runtime/state.py` 신설 또는 `schema.py` 확장).
