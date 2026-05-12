# Advisory Log: 2026-04-28 — M70 완료 및 M71 Correction Lifecycle 문서 동기화(Doc-Sync) 권고

## 개요
M70 Axis 1을 통해 `CorrectionHandlerMixin` 분리 작업이 성공적으로 완료되어 `app/handlers/aggregate.py`의 비대화 문제가 해소되었습니다. M61부터 M70까지 이어진 "교정 생명주기(Correction Lifecycle)" 강화 작업이 코드 수준에서는 완성 단계에 도달했으나, `docs/MILESTONES.md`와 `docs/TASK_BACKLOG.md`는 여전히 M49-M59 단계를 우선순위로 표기하고 있어 실질적인 진행 상황과 문서상의 "진실(Truth)" 사이에 큰 격차가 발생했습니다. 본 advisory는 이를 정합화하기 위한 M71 문서 동기화 슬라이스를 권고합니다.

## 분석 및 상태 확인
- **M70 성과**: 핸들러 구조 분리로 유지보수성을 확보했습니다. (verify CONTROL_SEQ 1249)
- **문서 부채**: `MILESTONES.md`는 M60 이후의 진행 상황(교정 통계, 요약, 목록, 검색, 승격 등)을 전혀 반영하지 못하고 있습니다. `TASK_BACKLOG.md` 역시 "Not Implemented" 항목이 이미 구현된 기능들을 포함하고 있어 혼란을 야기할 수 있습니다.
- **머지 백로그**: PR #54~#56을 포함해 6개 이상의 PR이 스택으로 쌓여 있어, 새로운 기능을 추가하기 전에 현재까지의 성과를 명확히 기록하고 "Truth-Sync"를 맞추는 것이 "v1.5 structural" 단계의 핵심 지침에 부합합니다.

## 권고 사항
`RECOMMEND: doc-sync M61–M70 Correction Lifecycle Truth-Sync`

### 권고 근거
1. **진실 정합성 (Truth-Sync)**: 코드 구현(M61–M70)과 문서(Milestones/Backlog)의 격차를 해소하여 파이프라인 운영의 모호성을 제거합니다. (Priority 1: same-family risk reduction)
2. **구조적 투명성**: "v1.5 structural" 단계에서 현재까지의 구조 개선 성과를 공식 기록하여 다음 Axis(예: Physical Validation 또는 Axis 3)를 위한 명확한 베이스라인을 구축합니다.
3. **백로그 가시화**: 쌓여 있는 PR 스택의 상태를 문서에 반영하여 운영자가 머지 우선순위를 판단할 수 있는 근거를 제공합니다.

### M71 상세 가이드
- **MILESTONES.md**: M60 (Task Log Schema)부터 M70 (Handler Decomp)까지의 완료 항목을 섹션별로 정리하여 기록. "Next 3 Priorities"를 현재 시점(M71 이후)에 맞춰 갱신.
- **TASK_BACKLOG.md**: 이미 완료된 "Correction-memory schema (TypedDict)", "Correction analytics" 등을 "Already Implemented"로 이동하고, 남은 "Physical validation" 등을 구체화.
- **Next Step 정의**: Correction Axis 종료 후 다음 주력 Axis(예: 모델 프롬프트 주입 신뢰도 또는 구조적 물리 검증)를 명문화.

## 결론
급격한 구현 속도로 인해 발생한 문서 부채를 청산하고 프로젝트의 나침반을 현재 위치로 옮기기 위해 M71 Doc-Sync 진행을 강력히 권고합니다.
