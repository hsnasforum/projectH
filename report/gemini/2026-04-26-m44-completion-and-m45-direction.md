# Advisory Log: 2026-04-26-m44-completion-and-m45-direction

## 요약
Milestone 44 (Applied Preference Transparency)의 구현 및 문서 동기화가 성공적으로 완료되었습니다. 로컬의 2개 커밋을 즉시 push하고 PR을 생성(안 A)하여 M44를 공식적으로 종료할 것을 권고합니다. 차기 Milestone 45의 방향으로 **후보 B (Preference 신뢰도 집계 UI)**를 선정하여, 기존에 수집된 신뢰도 통계를 시각화함으로써 사용자의 선호 관리 의사결정을 지원합니다.

## 분석 및 판단
1. **M44 완료 및 Publish 전략 (Q1)**:
   - M44 Axis 1/2를 통해 응답 팝오버에서의 선호 상태 및 전환 이유 표시가 완결되었습니다.
   - 로컬의 2개 커밋(`eb0c2ab`, `ec6af6e`)은 독립적인 기능 단위를 이루며, PR #37과 동일하게 즉시 publish하여 진실의 원천(Truth)을 동기화하는 것이 가장 안전한 경로입니다. (안 A 권고)

2. **M45 방향 선정 (Q2)**:
   - **선정: 후보 B (Preference 신뢰도 집계 UI)**.
   - `GEMINI.md`의 "same-family user-visible improvement" 및 "smallest coherent slice" 원칙에 가장 부합합니다.
   - 현재 `reliability_stats`(`applied_count`, `corrected_count`) 데이터가 이미 백엔드 페이로드에 포함되어 있으므로, 서버 변경을 최소화하면서 프론트엔드 UI(`PreferencePanel`) 확장만으로 높은 사용자 가치를 제공할 수 있습니다.
   - 이는 M43(상태 전환 감사)과 M44(적용 투명성)가 구축한 감사 루프를 통계적 요약(Summary)으로 확장하는 논리적 진화 단계입니다.

3. **향후 로드맵**:
   - `MILESTONES.md`의 "Next 3" 항목 2를 M45 Axis 1 (신뢰도 집계)로 승격하여 관리합니다.

## 권고 사항
- **RECOMMEND: Push M44 bundle (2 commits) and create/merge PR.**
  - `origin/feat/watcher-turn-state`로 push 후 `main` 병합 추진 (안 A).
- **RECOMMEND: Initiate Milestone 45 Axis 1 (Preference Reliability Summary UI).**
  - `PreferencePanel` 상단 또는 개별 항목에 "적용 대비 교정 성공률" 등을 시각적으로 표시.
  - 서버: 필요한 경우 `list_preferences_payload()`에서 전역 신뢰도 요약 데이터를 추가로 계산하여 전달.

## Exact Slice 권고
- **TASK**: Implement M45 Axis 1 (Preference Reliability Summary UI)
- **FILES**: `app/handlers/preferences.py`, `app/frontend/src/components/PreferencePanel.tsx`, `docs/MILESTONES.md`
- **CONTENT**: `PreferencePanel`에 선호별 신뢰도(성공률) 시각화; `MILESTONES.md` M45 섹션 추가.
