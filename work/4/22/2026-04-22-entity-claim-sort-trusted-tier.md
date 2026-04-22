# 2026-04-22 entity claim sort trusted tier

## 변경 파일
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/4/22/2026-04-22-entity-claim-sort-trusted-tier.md`

## 사용 skill
- `investigation-quality-audit`: entity-card primary claim selection의 source-role weighting 변경이 조사 품질 범위 안에 있는지 확인했습니다.
- `security-gate`: 변경이 read-only web investigation 정렬 로직에만 한정되고 승인/write/storage 경계를 바꾸지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증과 문서 동기화 필요성을 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 768의 exact slice에 따라 `core/agent_loop.py`의 `_entity_claim_sort_key()`를 `core/web_claims.py`의 `_claim_sort_key()` trusted-tier 계약과 맞췄습니다.
- entity-card primary claim selection에서 COMMUNITY/BLOG 같은 untrusted high-volume claim이 OFFICIAL/WIKI/DATABASE/DESCRIPTIVE trusted 단건 claim을 덮지 않도록 회귀 기준을 추가했습니다.

## 핵심 변경
- `_entity_claim_sort_key()` 반환 타입을 7-tuple로 확장했습니다.
- `claim.source_role in TRUSTED_CLAIM_SOURCE_ROLES` 여부를 `trusted_tier`로 계산해 정렬 키의 첫 기준으로 추가했습니다.
- inline `role_priority` dict와 `max()` call site는 handoff 제약에 따라 그대로 유지했습니다.
- `test_entity_claim_sort_key_trusted_beats_high_volume_untrusted`를 추가해 OFFICIAL 1건이 COMMUNITY 5건보다 entity-loop 정렬에서 우선되는지 검증했습니다.

## 검증
- `python3 -m py_compile core/agent_loop.py` 통과
- `python3 -m unittest tests.test_smoke` 통과 (`149 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- handoff 제약에 따라 docs와 `core/web_claims.py`, pipeline control 파일은 수정하지 않았습니다.
- 작업 시작 전부터 선행 라운드의 dirty tree가 남아 있어 전체 diff/status에는 이번 변경 외 파일들이 함께 보입니다.
