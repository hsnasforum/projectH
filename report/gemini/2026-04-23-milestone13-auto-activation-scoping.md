# 2026-04-23 Milestone 13 Auto-Activation & Merge Scoping

## 요약
- `feat/watcher-turn-state` 브랜치에 대한 풀스택 감사 결과, Milestone 9-12의 인프라가 완결되었으며 Milestone 13(개인화)을 위한 프롬프트 주입 코드도 이미 Shipped 상태임을 확인했습니다.
- 현재 개인화가 동작하지 않는 유일한 이유는 "활성화된 선호도(Active Preferences)"가 0개이기 때문입니다.
- 다음 단계로 **CANDIDATE에서 ACTIVE로의 자동 전환 로직(Axis 2)** 구현을 권고하며, 그 전에 현재 브랜치를 `main`으로 병합하여 베이스라인을 확정할 것을 제안합니다.

## 질문에 대한 답변

### a. CANDIDATE → ACTIVE 전환 로직 및 슬라이스
- **상태**: `storage/preference_store.py`에 수동 전환 메서드(`activate_preference`)는 있으나, 자동 트리거 로직은 없습니다.
- **슬라이스**: 가능합니다. `promote_from_corrections` 내부 또는 별도 헬퍼에서 `cross_session_count` 임계값(예: 3회) 도달 시 자동 활성화하도록 1개 파일(`storage/preference_store.py`) 수정으로 구현 가능합니다.

### b. Milestone 13 실질적 첫 구현 슬라이스
- **Axis 2: Auto-Activation Logic & Signal Thresholds**
- 프롬프트 주입은 이미 구현되어 있으므로, "수집된 후보(Candidate)를 언제부터 실제 모델에 적용(Active)할 것인가"에 대한 **자동 활성화 임계값 로직**을 연결하는 것이 M13의 가장 좁고 실질적인 다음 구현입니다.

### c. Merge 여부 판단
- **Merge to main 권고**: 현재 브랜치는 워처(watcher) 안정화와 마일스톤 9-12를 성공적으로 수행하여 28개 커밋이 쌓여 있습니다. 인프라가 완결된 이 시점에 `main`으로 병합하여 기술적 부채를 정리하고, M13 제품 기능은 깨끗한 상태에서 진행하는 것이 좋습니다.

## 권고 사항 (Milestone 13 Axis 2: Auto-Activation Logic)

### 핵심 변경 내용
- **파일**: `storage/preference_store.py`
- **구현**: `promote_from_corrections()` 메서드 하단에 `cross_session_count >= 3` 조건 충족 시 `self.activate_preference()`를 자동으로 호출하는 로직을 추가합니다.
- **테스트**: `tests/test_preference_store.py`에 다중 세션 반복 교정 시 자동 활성화 여부를 확인하는 테스트 케이스를 추가합니다.

## 판단 근거
- **Personalization 실현**: 137개의 교정 자산과 23개의 후보가 이미 존재하므로, 자동 활성화 로직만 연결되면 즉시 시스템 전체에 개인화 효과가 나타납니다.
- **가드레일 준수**: `MILESTONES.md`의 "repeated-signal promotion" 제약을 자동 활성화 임계값으로 구현하여 안전성을 확보합니다.
