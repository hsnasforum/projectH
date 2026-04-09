# docs: README project-brief PRODUCT_PROPOSAL MILESTONES NEXT_STEPS top-level response-feedback grounded-brief truth sync

## 변경 파일
- `README.md` — 2곳(line 8-11, 42-47): Current Shipped Contract + Current Product Slice에 response feedback + grounded-brief surface 추가
- `docs/project-brief.md` — 1곳(line 15): Current Contract 요약에 response feedback + grounded-brief surface 추가
- `docs/PRODUCT_PROPOSAL.md` — 1곳(line 25): Facts에 response feedback + grounded-brief surface 추가
- `docs/MILESTONES.md` — 1곳(line 6): Current Product에 response feedback + grounded-brief surface 추가
- `docs/NEXT_STEPS.md` — 1곳(line 5): browser MVP covers에 response feedback + grounded-brief surface 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 5개 파일의 top-level current product 요약에 shipped surface 2종 누락:
  - response feedback capture
  - grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, artifact-linked reject/reissue reason traces
- 이전 라운드에서 instruction docs (AGENTS, CLAUDE, PROJECT_CUSTOM_INSTRUCTIONS) 동기화 완료
- 근거 앵커: `README.md:57-62`, `docs/PRODUCT_SPEC.md:48-64`

## 핵심 변경
- 5개 파일 top-level 요약에 response feedback + grounded-brief trace/correction surface 추가
- structured correction memory나 durable preference memory 주장 없음
- 기존 스타일/간결성 유지 (README는 Korean, 나머지는 English)

## 검증
- `git diff --stat` — 5 files changed, 8 insertions(+), 3 deletions(-)
- `rg` — response feedback capture, grounded-brief artifact trace 모든 대상 파일 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 top-level current-summary response-feedback + grounded-brief 동기화 완료
