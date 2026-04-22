# 2026-04-22 milestone4-reinvestigation-done-next-scope

## 개요
CONTROL_SEQ 762(재조사 우선순위 최적화)가 완료됨에 따라, (1) 미커밋 작업의 번들 범위, (2) 다음 Milestone 4 구현 슬라이스(Axis 4)를 결정합니다.

## 중재 결과

### Q1 — Commit/push bundle scope
**RECOMMEND: commit_push_now_bundle_extended**
이미 완료된 Seqs 756(내부 필드), 759(UI 노출), 762(정렬 로직)는 모두 "Investigation Quality"라는 하나의 큰 주제로 묶이는 기능들입니다. 이 3개 슬라이스를 하나의 번들로 커밋 및 푸시하여 `feat/watcher-turn-state` 브랜치의 미커밋 작업 리스크를 해소하는 것을 권고합니다. 이는 개별 슬라이스가 모두 검증되었으므로 안전한 경계입니다.

### Q2 — Next Milestone 4 slice
**RECOMMEND: Axis 4: Source Role Weighting Refinement (Logic)**
다음 단계는 Milestone 4의 "stronger official/news/wiki/community weighting" 및 TASK_BACKLOG #2 "Prefer multi-source agreement over single-source noise"를 해결하기 위한 로직 개선입니다.
- **Entry Point:** `core/web_claims.py`의 `_claim_sort_key` (48행 부근)
- **Action:** 현재 `support_count`가 제1 정렬 기준이기 때문에, 다수의 비신뢰 출처(Blog, Community)가 단일 공식 출처(Official)를 이기고 primary claim으로 선정되는 "noise dominance" 문제가 있습니다.
- **Slice Scope:** `_claim_sort_key`에서 `role_priority`의 가중치를 높이거나 정렬 순서를 조정하여, 신뢰도가 높은 출처의 값이 소수의 지지만으로도 "다수 소음"보다 우선적으로 선택되도록 개선합니다. 이는 엔티티 카드의 진실성을 확보하는 핵심 로직입니다.

## 권고 요약
1. Seqs 756+759+762를 하나의 "Investigation Quality Bundle"로 묶어 커밋 및 푸시합니다.
2. 다음 슬라이스로 `core/web_claims.py`의 `_claim_sort_key`를 수정하여 출처 품질(Source Role)에 따른 가중치를 강화합니다.
3. 이를 통해 비신뢰 출처의 다수 의견이 공식 출처의 단일 의견을 가리는 현상을 방지합니다.
