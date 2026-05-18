# Advisory Log: 2026-04-28 — M68 완료 및 M69 교정 충돌 감지 및 검색 방향 권고

## 개요
M68 (Pattern-level Promotion) 마일스톤이 Axis 1+2를 통해 구현 및 검증되었으며, 관련 PR 번들 발행 과정에서 발생한 런타임 제어 정규화 문제(commit_push_pr_creation_m68_bundle stall)도 'Retriage' 라운드를 통해 해결되었습니다. 현재 파이프라인은 M68 성과를 반영한 상태로 정상화되었습니다. 본 advisory는 M61-M68로 이어온 "교정 가시성 및 생명주기" Axis를 마무리하고, 운영 안정성을 높이기 위한 M69 방향을 확정합니다.

## 분석 및 상태 확인
- **M68 성과**: 운영자가 승인된 교정 패턴을 즉시 `PreferenceRecord`로 승격시킬 수 있는 기능이 구현되었습니다. 이로써 "교정 -> 검증 -> 승격"의 데이터 루프가 완성되었습니다.
- **현 상황**:
  - **가시성 제약**: 현재 UI는 최근 3개의 교정 기록만 노출(M67)하고 있어, 과거의 중요한 패턴을 찾아 승격시키거나 관리할 방법이 부족합니다.
  - **충돌 위험**: 교정 패턴 승격 시 기존에 활성화된 선호도(`ACTIVE` Preferences)와의 충돌 여부를 사전에 확인하는 가드레일이 없습니다.
  - **머지 백로그**: #47, #48, #49 등 다수의 PR이 대기 중이며, M60-M68 성과가 `main`에 통합되기 전까지 브랜치 파편화 위험이 존재합니다.

## 권고 사항
`RECOMMEND: implement M69 Axis 1 — Correction Pattern Conflict Detection & Search`

### 권고 근거
1. **위험 감소 (Risk Reduction)**: 승격 과정에서 발생할 수 있는 선호도 간 충돌을 사전에 시각화하여 데이터 정합성을 보호합니다 (Priority 1: same-family risk reduction).
2. **운영 효율성 (User-visible Improvement)**: 검색 기능을 통해 과거 교정 이력에 대한 접근성을 확보하여 "Correction Lifecycle"의 실용성을 완성합니다.
3. **Axis 종결**: M61부터 시작된 교정 Axis의 마지막 고도화 단계로서, 이후에는 "PR 머지 백로그" 해소 및 "Axis 3: 모델 주입 신뢰도"로의 전환을 준비해야 합니다.

### M69 Axis 1 상세 가이드
- **기능**:
  - **Search**: `GET /api/corrections/list`에 `query` 파라미터를 추가하여 텍스트 검색 및 상태별 필터링 지원.
  - **Conflict Guard**: `GET /api/corrections/summary` 또는 `list`에서 각 패턴이 기존 `ACTIVE` 선호도와 갖는 Jaccard 유사도를 계산하여 충돌 위험(`has_conflict`) 표시.
- **Backend**: `AggregateHandlerMixin`에 검색 및 충돌 감지 로직 통합.
- **Frontend**: `PreferencePanel.tsx`에 교정 검색 필드 및 충돌 배지 추가.

## 결론
M68을 통해 확보된 승격 기능을 안전하고 효율적으로 확장하기 위해 M69 Axis 1 진행을 권고합니다. 또한, 현재 브랜치 파편화를 막기 위해 운영자가 대기 중인 PR 스택(#47, #48, #49)을 순차적으로 머지할 것을 병행 권고합니다.
