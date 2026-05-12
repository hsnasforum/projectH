# Advisory Log: 2026-04-26-m43-completion-and-m44-direction

## 요약
Milestone 43 (Preference Transition Auditability)의 모든 구현 및 문서 동기화가 완료되었습니다. 로컬의 5개 커밋을 즉시 push하고 PR을 생성(안 A)하여 M43을 공식적으로 종료할 것을 권고합니다. 차기 Milestone 44의 방향으로 **후보 A (Preference 적용 투명성 강화)**를 선정하여, 응답에 반영된 선호의 구체적 내용을 UI에 노출함으로써 감사 루프를 확장합니다.

## 분석 및 판단
1. **M43 완료 및 Publish 전략 (Q1)**:
   - M43 Axis 1/2를 통해 상태 전환 이유 기록 및 표시가 완결되었습니다.
   - 로컬에 누적된 5개 커밋(`ec4096b`~`ed10f6a`)은 기능적/문서적으로 일관된 번들이며, PR #36과 마찬가지로 즉시 병합하는 것이 리스크 감소 및 추적성 확보 면에서 유리합니다. (안 A 권고)

2. **M44 방향 선정 (Q2)**:
   - **선정: 후보 A (Preference 적용 투명성)**.
   - `GEMINI.md`의 "same-family user-visible improvement" 원칙에 가장 부합합니다. M43이 "왜 상태가 변했는가"를 다뤘다면, M44는 "현재 응답에 어떤 선호가 실제로 쓰였는가"를 상세히 보여줌으로써 사용자 통제권을 강화합니다.
   - `applied_preferences` 페이로드는 이미 존재하므로, 서버의 `AgentResponse` 생성부와 프론트엔드 메시지 UI 확장으로 범위를 좁혀 구현 가능합니다.

3. **우선순위 및 로드맵**:
   - `MILESTONES.md`의 "Next 3" 항목 2를 M44 Axis 1 (적용 투명성)로 승격하여 프로젝트 진실의 원천을 유지합니다.

## 권고 사항
- **RECOMMEND: Push M43 bundle (5 commits) and create/merge PR.**
  - `origin/feat/watcher-turn-state`로 push 후 main 병합 추진.
- **RECOMMEND: Initiate Milestone 44 Axis 1 (Preference Application Transparency).**
  - 응답에 포함된 `applied_preferences` 뱃지에 마우스 오버/상세 보기 시, 반영된 각 선호의 `description` 및 `fingerprint` 노출.
  - 서버: `chat.py` 등에서 응답 생성 시 반영된 선호 상세 정보를 페이로드에 포함하도록 보강.

## Exact Slice 권고
- **TASK**: Implement M44 Axis 1 (Preference Application Transparency)
- **FILES**: `app/handlers/chat.py` (또는 관련 응답 생성부), `app/frontend/src/components/MessageBubble.tsx`, `docs/MILESTONES.md`
- **CONTENT**: `MessageBubble`의 적용 선호 뱃지 인터랙션 강화; 개별 선호 내용 노출; `MILESTONES.md` M44 섹션 추가.
