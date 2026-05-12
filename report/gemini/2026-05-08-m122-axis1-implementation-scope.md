# 2026-05-08 M122 차기 슬라이스 구현 진입 (M122 Axis 1) — Advisory

## Status
- **M121 완료**: Watcher lease reclamation 구현 및 PR #117 머지 완료.
- **문서 동기화**: `docs/MILESTONES.md`의 `Next 3 Implementation Priorities` 최신화 완료 (M122 진입 명시).
- **잔존 Gap**: `docs/TASK_BACKLOG.md`의 `Next 3` 섹션이 stale 상태이나, `Implemented` 및 `Current Phase` 섹션이 M122 방향을 지지하고 있어 구현 진입에는 무리가 없음.

## Recommendation

### RECOMMEND: implement M122 Axis 1 (Multi-source agreement backend logic)

#### 1. 대상 파일 및 역할
- **`core/agent_loop.py`**:
    - `_entity_source_fact_agreement_score`: 소스 간 합의 점수 계산 로직 강화. 신뢰할 수 있는 소스 간의 합의에 더 높은 가중치 부여.
    - `_entity_trust_score` 및 소스 정렬(`decorated` score): 합의 점수(agreement_score)의 비중을 높여, 단일 신뢰 소스보다 다수 소스의 합의 정보가 우선적으로 선택되도록 개선.
- **`core/web_claims.py`**:
    - `summarize_slot_coverage`: `CoverageStatus.STRONG` 판단 기준 정교화. 단순히 count 기반이 아닌, 소스의 신뢰도와 합의 여부를 더 엄격하게 반영.
    - `CoverageStatus` 확장 또는 레이블링 로직 개선 (단일 신뢰 소스 vs 합의된 강한 사실 구분 준비).

#### 2. Axis 1 구현 범위
- **Backend Logic 우선**: UI 변경 없이 백엔드에서의 소스 랭킹, 합의 점수 산정, 슬롯 커버리지 상태 결정 로직을 고도화하는 데 집중합니다.
- **노이즈 억제**: 커뮤니티/블로그 등 저신뢰 소스가 단독으로 정보를 제공할 경우의 가중치를 낮추고, 다른 소스와의 합의가 없을 시 `STRONG` 상태가 되지 않도록 제약 강화.

#### 3. 검증 방법
- **Unit Tests**: `core/web_claims.py`의 `summarize_slot_coverage`를 대상으로 다양한 소스 조합(합의 vs 단일 신뢰 vs 노이즈)에 대한 상태 판정 테스트 코드 추가.
- **Agent Loop Test**: `_entity_source_fact_agreement_score`가 의도한 가중치를 생성하는지 확인하는 로직 테스트.

#### 4. Axis 2 예정 범위
- **UI Visibility**: 개선된 백엔드 상태를 바탕으로 프런트엔드 배지 및 툴팁 설명(Plain-language explanation) 강화.

## Decision Rationale
- M121 인프라 개선이 완료됨에 따라 제품 본연의 가치인 "웹 조사 품질" 개선으로 회귀합니다.
- Axis 1에서 백엔드 로직을 먼저 단단하게 다져놓아야 Axis 2의 UI 개선이 실질적인 데이터 기반으로 사용자에게 신뢰를 줄 수 있습니다.

## Stop Rule
- 로직 개선이 웹 조사(entity-card) 외의 일반 로컬 문서 요약 품질을 저하시키는 경우 중단.
- `TASK_BACKLOG.md`의 우선순위 불일치로 인해 구현 중 범위 혼선이 발생할 경우 `doc-sync` 우선 수행.
