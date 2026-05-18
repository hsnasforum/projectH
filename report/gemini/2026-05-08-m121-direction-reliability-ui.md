# 2026-05-08 M121 Direction (Reliability UI) — advisory

## STATUS: advice_ready
## CONTROL_SEQ: 1551

---

## 개요
M119 Axis 2(배지 UI)와 NBSP fix의 문서 동기화가 완료되었습니다. 현재 PR #113, #114, #115가 스택 구조로 대기 중이며, M120의 백엔드 신뢰도 필터(Axis 1)는 구현되었으나 사용자에게 그 강등 근거를 알리는 UI가 부재한 상태입니다.

## 추천 사항
**RECOMMEND: implement M120 Axis 2 (Reliability UI 표시)**

### 근거
1. **기능적 완결성**: M120 Axis 1에서 구현된 '신뢰도 강등' 로직은 현재 사용자에게 결과(배지 사라짐)만 보여줄 뿐, 그 원인(주입 대비 교정률 높음)을 설명하지 못합니다. M120 Axis 2를 통해 이 피드백 루프의 가시성을 확보해야 합니다.
2. **패턴 유지**: M118/M119에서 수행한 'API/데이터(Axis 1) → UI/배지(Axis 2)'의 점진적 구현 패턴을 유지하여 마일스톤을 깔끔하게 마무리할 수 있습니다.
3. **리스크 우선순위**: 후보 A(Watcher Lease fix)는 중요한 내부 인프라 개선 사항이나, 현재 진행 중인 "주입-교정 피드백 루프"라는 제품 기능 테마의 완결이 사용자 가치 측면에서 더 우선됩니다.

## 실행 전략 (Implement Handoff 힌트)
- **범위**: `app/frontend/src/components/PreferencePanel.tsx` 수정.
- **내용**:
    - `is_highly_reliable`이 강제로 `false`가 된 경우(즉, `injection_correction_rate > 0.25` 등 M120 조건 충족 시), 사용자에게 "높은 교정률로 인해 신뢰도 강등됨"과 같은 툴팁이나 보조 텍스트를 제공합니다.
    - 기존 M119 배지(`N회 주입 (A% 적용 · R% 교정)`)와 결합하여 자연스럽게 노출되도록 조정합니다.
- **검증**:
    - `PreferencePanel.tsx` 유닛 테스트 또는 targeted E2E (M120 조건 픽스처 사용).
    - EROFS 환경 제약으로 인한 `/tmp` 빌드 우회 절차를 준수합니다.

## 다음 단계
1. **M120 Axis 2 구현**: 위 가이드에 따라 UI 슬라이스 진행.
2. **Internal Cleanup (Candidate A)**: M120 Axis 2 완료 후, 또는 PR merge gate 대기 시간 중 별도 슬라이스로 Watcher Lease TTL 개선 진행 권장.
3. **Merge Gate**: PR #113~#115의 `pr_merge_gate` operator 승인 및 머지 진행.
