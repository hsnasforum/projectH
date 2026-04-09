# docs: PRODUCT_SPEC ACCEPTANCE_CRITERIA reviewed-memory entry-slice historical wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 2곳(line 415, 970): entry-slice 역사적 문구에서 shipped reviewed-memory surface 부정 제거
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 186): entry-slice 역사적 문구에서 shipped reviewed-memory surface 부정 제거

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- PRODUCT_SPEC:415 — "no review queue"로 적어 shipped review queue를 부정
- PRODUCT_SPEC:970 — "reviewed memory and user-level memory still remain closed"로 적어 shipped reviewed-memory를 미출하로 프레이밍
- ACCEPTANCE_CRITERIA:186 — "first implementation slice is `artifact_id` linkage, not review queue"로 적어 shipped review queue를 부정
- 실제 shipped truth: review queue, aggregate apply trigger, active-effect path 이미 출하; user-level memory만 later

## 핵심 변경
- PRODUCT_SPEC:415 — "no review queue" → "review queue (`검토 후보`) and aggregate apply trigger (`검토 메모 적용 후보`) are now shipped in later slices above this entry slice"
- PRODUCT_SPEC:970 — "reviewed memory and user-level memory still remain closed" → "reviewed-memory first slice is now shipped; user-level memory still remains later"
- ACCEPTANCE_CRITERIA:186 — "first implementation slice is `artifact_id` linkage, not review queue" → "first implementation slice was `artifact_id` linkage; review queue, aggregate apply trigger, and active-effect path are now shipped in later slices. User-level memory still remains later."
- user-level memory later 유지

## 검증
- `git diff --stat` — 2 files changed, 3 insertions(+), 3 deletions(-)
- `rg` stale phrases — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — PRODUCT_SPEC/ACCEPTANCE_CRITERIA의 reviewed-memory entry-slice historical wording 동기화 완료
