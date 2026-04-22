# 2026-04-22 milestone4-weighting-done-scope

## 개요
CONTROL_SEQ 765(Source Role Weighting)가 `core/web_claims.py`에 구현됨에 따라 Milestone 4의 주요 품질 축이 대부분 확보되었습니다. 하지만 `AgentLoop`와의 로직 불일치(drift)가 발견되어 Milestone 4 완료 여부와 다음 슬라이스 범위를 중재합니다.

## 중재 결과

### Q1 — Milestone 4 completion status
**Milestone 4는 아직 완전히 완료되지 않았습니다.**
- **로직 불일치(Logic Drift):** `core/web_claims.py`의 `_claim_sort_key`는 seq 765에서 7-tuple(`trusted_tier` 포함)로 확장되었으나, `core/agent_loop.py`의 `_entity_claim_sort_key`(4134행)는 여전히 이전의 6-tuple 형상을 유지하고 있습니다. 이로 인해 엔티티 카드에 표시할 대표값(primary claim) 선택 시 "신뢰 출처 우선" 원칙이 적용되지 않는 불일치가 발생합니다.
- **UI 노출(UI Exposure):** `source_role`과 `trust_tier` 데이터가 API로 전달되고 있으나, `MessageBubble.tsx` 등 프론트엔드에서 이를 실제 텍스트나 툴팁으로 노출하는 "source role labeling" 작업이 남아 있습니다.
- **Actionable Hints:** `AGENTS.md`에서 언급된 "actionable hints"와 상세한 재조사 설명이 UI 상에서 명확히 확인되지 않습니다.

### Q2 — Commit/push bundle scope
**RECOMMEND: defer_commit_push**
`AgentLoop`의 정렬 로직 불일치는 시스템 전체의 진실성(truthfulness)을 저해하는 핵심 결함입니다. 이 drift를 해결하는 슬라이스를 하나 더 실행하여 Milestone 4의 "Weighting" 품질을 전체 시스템에 동기화한 후, 756+759+762+765+α를 하나의 큰 Milestone 4 번들로 커밋 및 푸시하는 것을 권고합니다.

### Q3 — Next Milestone 4 slice
**NEXT SLICE: AgentLoop sort-key truth-sync (Axis 4 Completion)**
- **Entry Point:** `core/agent_loop.py` line 4134 (`_entity_claim_sort_key`)
- **Action:** `_entity_claim_sort_key`의 반환 타입을 7-tuple로 확장하고, `core/web_claims.py`와 동일하게 `trusted_tier`를 첫 번째 정렬 기준으로 도입합니다. 또한 중복 정의된 `role_priority` 상수를 `core/web_claims.py`에서 임포트하거나 공유하도록 통합합니다.
- **이유:** 이 작업을 통해 커버리지 점수(web_claims)와 실제 표시되는 대표값(AgentLoop)의 선택 기준이 일치하게 되어, 다수의 소음(noise)이 공식 출처(Official)를 가리는 현상을 시스템 전체에서 방지할 수 있습니다.

## 권고 요약
1. 커밋/푸시를 보류하고 `AgentLoop` 정렬 로직 동기화 슬라이스를 먼저 진행합니다.
2. `core/agent_loop.py`의 `_entity_claim_sort_key`를 `core/web_claims.py` 수준으로 고도화합니다.
3. 이후 "source role labeling" UI 노출을 통해 Milestone 4를 최종 클로징합니다.
