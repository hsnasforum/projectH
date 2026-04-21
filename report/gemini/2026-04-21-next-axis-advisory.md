# 2026-04-21 차기 구현 축(Axis) 선정 권고

## 개요
- AXIS-G4, G5-silent, G11(SQLiteSessionStore adoption audit) 시리즈가 완료되었습니다.
- verify-lane은 현재 G6(PermissionError) 조사, Dispatcher Trace Backfill(무결성 체크), G4 E2E(런타임 확인)를 수행 중입니다.
- `tests/test_pipeline_runtime_supervisor.py`에서 발견된 106 vs 104 테스트 카운트 불일치(Undocumented tests)와 미룬 과제인 `COMMUNITY` 어휘 명시화를 해결하기 위한 차기 슬라이스를 선정합니다.

## 판단 근거
1. **Technical Integrity (Truth-Sync)**: `tests/test_pipeline_runtime_supervisor.py`에 존재하는 2개의 "미기록" 테스트는 사실 4월 20일 G7 및 Autonomy 안정화 라운드에서 추가된 것입니다. 그러나 현재 verify-lane이 이를 "scope violation"으로 인지하고 있어, 파이프라인의 baseline을 106으로 정직하게 재설정(Truth-Sync)하는 과정이 시급합니다.
2. **Readability & Consistency (AXIS-G10)**: `core/agent_loop.py`의 `role_confidence` 맵에서 `SourceRole.COMMUNITY`가 여전히 implicit fallback(0.4)에 의존하고 있습니다. 이를 명시적 키로 추가하여 `_ROLE_PRIORITY`와의 정합성을 높이고 코드 가독성을 개선합니다.
3. **병렬성**: 이 작업은 `core/` 및 `tests/` 레이어의 격리된 수정으로, verify-lane이 진행 중인 G6 조사나 런타임 확인과 충돌 없이 병렬 진행이 가능합니다.

## 권고 (RECOMMEND)
- **AXIS-G13 (Truth-Sync: Supervisor Test Baseline 106) 및 AXIS-G10 (role_confidence COMMUNITY)**
- **이유**: 파이프라인의 테스트 baseline을 106개로 공식화하여 "undocumented diff" 리스크를 해소하고, 미뤄둔 `COMMUNITY` 역할의 신뢰도 가중치를 명시적으로 고정합니다.

### 세부 지시 사항
1. **AXIS-G13 (Truth-Sync)**:
   - `tests/test_pipeline_runtime_supervisor.py`의 현재 상태(106 tests)를 baseline으로 수용합니다.
   - `/work` 노트를 통해 해당 테스트들이 이전 라운드 산출물임을 명시하여 "Truth Gap"을 닫습니다.
2. **AXIS-G10 (Readability)**:
   - `core/agent_loop.py`의 `_build_entity_claim_records` 내 `role_confidence` 맵에 `SourceRole.COMMUNITY: 0.4`를 명시적으로 추가합니다.
   - `tests/test_smoke.py`의 관련 테스트(`test_build_entity_claim_records_role_confidence_aligns_with_role_priority_hierarchy`)에서 `COMMUNITY`에 대한 assertion을 추가하여 고정합니다.

## 결론
G13/G10 복합 슬라이스를 통해 누적된 기술 부채(Truth Gap 및 가독성 미비)를 정리하고, verify-lane의 G6 조사 결과가 나올 때까지 구현 레인을 생산적으로 유지할 것을 권고합니다.
