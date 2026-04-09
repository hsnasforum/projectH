# docs: project-brief PRODUCT_PROPOSAL grounded-brief current-vs-next truth sync

## 변경 파일
- `docs/project-brief.md` — "Not Implemented" 섹션에서 shipped 항목 분리하여 "Already Shipped Foundations" 추가
- `docs/PRODUCT_PROPOSAL.md` — "Needed Next" 섹션에서 shipped 항목 분리하여 "Already Shipped Foundations" 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- project-brief.md:91 — "`grounded brief` artifact identity"를 "Not Implemented"로 분류했으나 `artifact_id`/`artifact_kind`/`source_message_id` trace anchor는 이미 출하
- PRODUCT_PROPOSAL.md:144-147 — "grounded-brief artifact snapshots", "corrected output pairs", "artifact-linked rejection reasons"를 "Needed Next"로 분류했으나 `original_response_snapshot`, `corrected_outcome`, `approval_reason_record`, `content_reason_record` 등은 이미 출하
- 근거 앵커: `README.md:58-59`, `docs/PRODUCT_SPEC.md:49-53`, `docs/PRODUCT_SPEC.md:524-559`, `docs/PRODUCT_SPEC.md:301-653`

## 핵심 변경
- 양쪽 파일에 "Already Shipped Foundations" 섹션 추가:
  - grounded-brief artifact trace anchors
  - original-response snapshot and corrected-outcome capture
  - artifact-linked reject / reissue reason traces
  - corrected-save linkage
- "structured correction-memory schema"는 "(beyond current trace foundations)" 수식어와 함께 Not Implemented / Needed Next 유지
- "durable preference-rule candidates"는 Needed Next 유지
- "corrected output pairs", "artifact-linked rejection reasons"는 Needed Next에서 제거 (이미 shipped)

## 검증
- `git diff --stat` — 2 files changed, 14 insertions(+), 5 deletions(-)
- `rg` — shipped 항목이 적절한 섹션에 위치 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — project-brief/PRODUCT_PROPOSAL의 grounded-brief current-vs-next 진실 동기화 완료
