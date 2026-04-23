# 2026-04-23 Milestone 12 이후 차기 작업축 (Personalization Activation)

## 요약
- Milestone 12 "Personalized Local Model Layer"의 모든 축(1-6)이 완료되어, 137개의 고품질 교정 쌍이 자산화(Promoted)되었습니다.
- 평가 결과(`JUSTIFIED`)에 따라 모델 레이어 도입의 정당성이 확보되었으므로, 다음 단계인 **실제 개인화 적용(Milestone 13)**으로의 전환을 권고합니다.
- `feat/watcher-turn-state` 브랜치의 인프라는 이미 안정화되었으며, 현재는 제품 기능(Product Milestone) 구현의 안정적인 베이스라인 역할을 하고 있습니다.

## 질문에 대한 답변

### a. Milestone 12 이후 가장 작은 포지티브 next slice
- **Milestone 13 Axis 1: Model Prompt Augmentation (Active Preference Injection)**
- 이미 승격된 137개의 교정 자산과 23개의 선호도 후보를 실제 비서(Assistant)의 프롬프트에 주입하여 개인화된 응답을 생성하기 시작하는 단계입니다.
- 워처(watcher)의 turn-state는 현재 자동화 파이프라인(IMPLEMENT, VERIFY 등)을 완벽히 지원하고 있으며, 추가적인 인프라 수정 없이 새 마일스톤 구현이 가능합니다.

### b. Bounded 1-2 파일 구현 핸드오프 가능 여부
- **가능합니다.** `app/handlers/chat.py` 단일 파일 수정으로 프롬프트 주입 기능을 구현할 수 있습니다.
- `PreferenceStore`에서 `active` 상태인 선호도를 가져와 시스템 프롬프트 끝에 덧붙이는 방식은 매우 좁고 안전한 구현 슬라이스입니다.
- **사유**: 인프라(M12)가 준비되었고 데이터가 JUSTIFIED 판정을 받았으므로, 이제는 사용자가 "개인화"를 체감할 수 있는 실질적인 기능을 여는 것이 최우선입니다.

### c. `feat/watcher-turn-state` 브랜치 상태 판단
- **완료 및 안정화 상태**: 브랜치 이름이 암시하는 워처의 턴 상태 관리 기능은 Milestone 9-12를 거치며 이미 완결되었습니다 (seq 753 부근에서 이미 안정화).
- 현재 브랜치는 워처 자체의 실험이 아닌, 워처가 제공하는 3-agent 자동화 환경 위에서 제품 마일스톤을 구현하는 **통합 구현 브랜치**로 기능하고 있습니다.

## 권고 사항 (Milestone 13 Axis 1: Model Prompt Augmentation)

### 핵심 변경 내용
- **파일**: `app/handlers/chat.py`
- **구현**: 비서 응답 생성 시 `PreferenceStore.get_active_preferences()`를 호출하여 활성화된 선호도 목록을 가져오고, 이를 시스템 프롬프트(system prompt)에 "사용자 맞춤형 지침" 섹션으로 추가합니다.
- **테스트**: `tests/test_smoke.py` 또는 신규 단위 테스트를 통해 프롬프트에 활성 선호도가 포함되는지 확인합니다.

## 판단 근거
- **데이터 활용**: 137개의 승격된 자산이 `CorrectionStore`에만 머물지 않고 실제 응답 품질 개선에 기여하게 만드는 가장 빠른 경로입니다.
- **Precondition 만족**: Axis 6에서 데이터 충분성이 입증되었으므로, 모델 레이어 활성화 지연은 더 이상 필요하지 않습니다.
