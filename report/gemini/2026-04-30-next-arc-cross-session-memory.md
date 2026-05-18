# 2026-04-30 차기 구현 아크 방향 권고 — Cross-session Memory

## 1. 개요

- **권고 방향**: **A) cross-session memory 강화**
- **근거**: Milestone 113(Review Queue UX) 완결로 세션 내 메모리(same-session recurrence) 기반이 확립되었습니다. '학습 가능한 로컬 개인화 에이전트'라는 북극성(North Star) 목표를 달성하기 위해, 단일 세션의 휘발성 지식을 영구적인 '개인 선호(Preference)'로 승격하고 이를 고품질로 활용하는 단계가 시급합니다.
- **병합 대기 관련**: 현재 PR #103–#106은 주로 프론트엔드 UI 및 문서 업데이트에 집중되어 있어, `core/agent_loop.py`나 `storage/preference_store.py`를 다루는 차기 아크 구현을 병렬로 시작해도 충돌 위험이 낮습니다.

## 2. 상세 권고 내역

### 방향 선정 이유
1. **북극성 목표 정렬**: 사용자 교정을 학습하여 미래 응답에 반영하는 '가르칠 수 있는 에이전트'의 핵심 가치는 세션 간 지식 전이에 있습니다.
2. **기술적 준비성**: `PreferenceStore`와 `CorrectionStore` 등 기초 저장소 구조가 이미 존재하며, 최근 업데이트된 OpenAI prompt guidance(root memory 반영 완료)를 통해 더 세련된 선호도 주입 전략을 적용할 적기입니다.
3. **사용자 가치**: '선호 N건 반영' 배지가 표시되는 것에 그치지 않고, 실제로 사용자가 체감할 수 있는 응답 품질의 변화를 만들어내는 것이 다음 품질 축(Quality Axis)입니다.

### 첫 번째 슬라이스 제안
- **슬라이스명**: `cross-session-preference-injection-fidelity`
- **범위**: 활성 선호의 세션 간 주입 품질 개선 (Inject active preferences with higher fidelity)
- **주요 작업**:
  - `core/agent_loop.py`의 `_get_active_preferences` 로직 강화: 단순 텍스트 나열을 넘어, 현재 컨텍스트와 관련성이 높은 선호를 선택하는 기초적인 선택 로직 또는 더 명확한 시스템 프롬프트 구성 지침 적용.
  - 주입된 선호가 실제 응답 생성에 어떻게 기여했는지 확인할 수 있는 최소한의 내부 트레이스(Task Log) 강화.
  - `is_highly_reliable=True` 조건 외에, 사용자가 명시적으로 'Accept'한 검토 후보가 자동 활성화(3회 반복)될 때의 주입 우선순위 조정.

## 3. 리스크 및 대응

- **PR 병합 충돌**: `app/frontend/src/` 및 E2E 테스트 파일에서 미세한 충돌이 발생할 수 있으나, 백엔드 로직 중심의 첫 슬라이스를 진행함으로써 리스크를 최소화합니다.
- **프롬프트 오버헤드**: 선호도가 너무 많이 주입되어 컨텍스트를 낭비하지 않도록, `budget` 기반의 엄격한 관리를 유지합니다.

---
**STATUS**: advice_ready
**CONTROL_SEQ**: 1512
**RECOMMEND**: implement m114_cross_session_memory_injection_fidelity
