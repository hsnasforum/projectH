# 2026-04-22 claim sort trusted tier

## 변경 파일
- `core/web_claims.py`
- `tests/test_smoke.py`
- `work/4/22/2026-04-22-claim-sort-trusted-tier.md`

## 사용 skill
- `investigation-quality-audit`: claim primary selection의 source-role weighting 변경이 Milestone 4 조사 품질 범위 안에 있는지 확인했습니다.
- `security-gate`: 변경이 web investigation의 read-only 정렬 로직에만 한정되고 승인/write/storage 경계를 바꾸지 않는지 확인했습니다.
- `finalize-lite`: 구현 종료 전 실행한 검증과 문서 동기화 필요성을 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 765의 exact slice에 따라 `_claim_sort_key()`가 untrusted high-volume source보다 trusted source를 primary claim으로 우선하도록 조정했습니다.
- Milestone 4의 stronger official/news/wiki/community weighting 범위에서 COMMUNITY/BLOG/PORTAL 다건 신호가 OFFICIAL/WIKI/DATABASE/DESCRIPTIVE 단건 신호를 덮지 않게 하는 회귀 기준이 필요했습니다.

## 핵심 변경
- `_claim_sort_key()` 반환 타입을 7-tuple로 확장했습니다.
- `record.source_role in TRUSTED_CLAIM_SOURCE_ROLES` 여부를 `trusted_tier`로 계산해 정렬 키의 첫 기준으로 추가했습니다.
- 같은 trusted tier 내부에서는 기존처럼 `support_count`가 먼저 적용되도록 기존 우선순위 순서를 유지했습니다.
- `test_claim_sort_key_trusted_source_beats_high_volume_untrusted`를 추가해 OFFICIAL 1건이 COMMUNITY 5건보다 primary로 선택되는지 검증했습니다.
- `test_claim_sort_key_higher_support_wins_within_trusted_tier`를 추가해 trusted tier 내부에서는 support volume이 계속 우선되는지 검증했습니다.

## 검증
- `python3 -m py_compile core/web_claims.py core/contracts.py` 통과
- `python3 -m unittest tests.test_smoke` 통과 (`148 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 라운드는 commit/push/PR을 수행하지 않았습니다.
- handoff 제약에 따라 docs는 수정하지 않았습니다. `docs/MILESTONES.md`의 Milestone 4 항목은 이미 stronger official/news/wiki/community weighting을 현재 범위로 적고 있습니다.
- 작업 시작 전부터 선행 라운드의 dirty tree가 남아 있어 전체 diff/status에는 이번 변경 외 파일들이 함께 보입니다.
