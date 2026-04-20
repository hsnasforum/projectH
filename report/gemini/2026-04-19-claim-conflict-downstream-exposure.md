# 2026-04-19 claim conflict downstream exposure

## 개요
- **Arbitration 대상**: Seq 367 차기 slice 결정
- **결정**: Option B (`Agent Loop Coverage Status CONFLICT Labeling`) 선택
- **Exact Slice**: `core/agent_loop.py: handle CoverageStatus.CONFLICT in internal labels and ranks`

## 판단 근거
1. **우선순위 (Risk Reduction & User Improvement)**: 현재 `CoverageStatus.CONFLICT`는 core contract 레벨에는 추가되었으나, `agent_loop.py` 내부 로직에서는 여전히 `WEAK`로 취급되거나 "단일 출처"로 평탄화되어 표시되고 있습니다. 이는 신뢰할 만한 출처들 사이의 '정보 상충'을 단순히 '증거 부족'으로 오인하게 만드는 리스크가 있으므로, Option A(단순 summary counter 추가)보다 우선순위가 높습니다.
2. **에이전트 인지력 강화**: `_claim_coverage_status_rank`와 `_claim_coverage_status_label`을 업데이트함으로써 에이전트가 스스로의 조사 진행 상황을 더 정확히 인지하게 하고, `_build_claim_coverage_progress_summary`를 통해 사용자에게 구체적인 상충 상황을 알릴 수 있습니다.
3. **가독성 및 일관성**: 이전 라운드(Seq 366)에서 logic truth가 고정되었으므로, 이를 agent loop의 의사결정 및 로깅 지표에 반영하는 것이 family completion을 위한 자연스러운 순서입니다.

## 추천 Slice 상세
- **Title**: `Agent Loop Coverage Status CONFLICT Labeling`
- **목적**: `CONFLICT` 상태의 슬롯이 에이전트 루프 내에서 올바른 랭크(RANK)와 라벨(LABEL)을 갖게 하고, 진행 요약 문구에서 "정보 상충"으로 명시되도록 합니다.
- **범위**:
  - `core/agent_loop.py`:
    - `_claim_coverage_status_rank`: `CONFLICT`에 대한 랭크 정의 (STRONG과 WEAK 사이 또는 전용 랭크).
    - `_claim_coverage_status_label`: `CONFLICT` -> `"정보 상충"` 라벨 매핑 추가.
    - `_build_claim_coverage_progress_summary`: `CONFLICT` 상태를 unresolved set(`{WEAK, MISSING}`)에 포함하거나 별도 분기로 처리하여 재조사 필요성을 유지.
    - `_build_entity_slot_probe_queries`: (필요 시) `CONFLICT` 상태일 때의 특화된 쿼리 생성 로직 검토.
- **검증**: `AgentLoop` 헬퍼 메서드들에 대한 focused unittest (CONFLICT 입력 시 rank/label/summary 결과 확인), `py_compile`, `git diff --check`.

## 리스크 및 주의사항
- `app/serializers.py`의 카운터 업데이트(Option A)는 이번 slice에서 제외되므로, 히스토리 요약 카운트에서는 여전히 CONFLICT가 WEAK와 섞여 보일 수 있으나, 에이전트의 실시간 진행 로그와 내부 판단 로직은 이번 slice로 먼저 정상화됩니다.
- 한국어 조사(은/는, 이/가) 처리가 `progress_summary` 생성 시 자연스러운지 확인이 필요합니다.
