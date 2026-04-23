# 2026-04-23 Milestone 12 종료 및 Milestone 13 안전 루프 수립

## 요약
- Milestone 12 "Personalized Local Model Layer"의 인프라 및 평가 단계가 성공적으로 완료되었습니다.
- `feat/watcher-turn-state` 브랜치의 모든 성과를 `main`으로 병합(PR #27)하여 베이스라인을 확정할 것을 권고합니다.
- 다음 단계인 Milestone 13의 첫 구현 슬라이스로 **개인화 유효성 추적(Preference Effectiveness Tracking)**을 제안합니다. 이는 모델이 적용한 선호도가 실제 품질 개선으로 이어졌는지 감시하는 핵심 안전 루프입니다.

## 질문에 대한 답변

### a. OPEN QUESTION #3 전제 조건 충족 여부
**결과**: **충족됨**
**근거**: `app/handlers/aggregate.py`에 `reviewed_memory`의 전체 라이프사이클(Apply/Reversal/Conflict)이 구현되어 있으며, `storage/preference_store.py`가 `delta_fingerprint`를 통해 신뢰할 수 있는 재현 키(Truthful recurrence key)를 확보하고 있습니다. 따라서 기술적 전제 조건은 이미 Shipped 코드에 존재합니다.

### b. `cross_session_count >= 3` 자동 활성화 허용 여부
**판단**: `MILESTONES.md`의 Priority #3 제약에 따라 현재는 **의도적으로 보류(Deferred)**되는 것이 프로젝트의 일관성에 부합합니다. 비록 "later than conflict visibility" 조건은 충족되었으나, 자동 활성화 이전에 수동 활성화된 선호도의 품질을 검증하는 안전 장치(Axis 1)를 먼저 구축하는 것이 선행되어야 합니다.

### c. Milestone 13 최적의 첫 구현 슬라이스
**Axis 1: Preference Effectiveness Tracking (Safety Loop)**
- **구현**: `app/handlers/feedback.py`의 `submit_correction` 시 소스 메시지에 반영된 `applied_preferences`를 추출하여 `CorrectionStore` 레코드에 함께 저장합니다.
- **파일**: `app/handlers/feedback.py`, `storage/correction_store.py` (단 2개 파일)
- **사유**: 개인화가 모델 출력을 망가뜨리는 경우를 정량적으로 추적할 수 있게 함으로써 Milestone 12의 "safe and measurable" 약속을 운영 단계에서 실현합니다.

## 권고 사항 (PR Merge & Milestone 13 Axis 1)

### 핵심 변경 내용
1. **Axis 0 (PR Merge)**: PR #27을 머지하여 Milestone 9-12의 인프라 성과를 영구 자산화합니다.
2. **Axis 1 (Tracking)**: 사용자가 교정(Correction)을 제출할 때, 해당 메시지가 개인화된 응답이었는지 여부를 기록합니다.
   - `storage/correction_store.py`의 `record_correction()`에 `applied_preference_ids` 파라미터를 추가합니다.
   - `app/handlers/feedback.py`에서 `submit_correction` 처리 시 소스 메시지의 선호도 목록을 넘겨줍니다.

## 판단 근거
- **리스크 관리**: 대규모 인프라 변경(PR #27)을 확정한 후, 제품 기능(M13)을 새로운 베이스라인에서 시작하는 것이 기술적 부채를 최소화합니다.
- **안전 우선**: 자동 활성화(Thresholds)보다 개인화의 "실패"를 먼저 감지할 수 있는 능력을 갖추는 것이 안전한 AI 에이전트 개발의 핵심입니다.
