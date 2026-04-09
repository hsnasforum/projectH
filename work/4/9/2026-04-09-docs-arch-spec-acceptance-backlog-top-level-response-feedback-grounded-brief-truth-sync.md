# docs: ARCHITECTURE PRODUCT_SPEC ACCEPTANCE_CRITERIA TASK_BACKLOG top-level response-feedback grounded-brief truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 1곳(line 10): Current Contract에 response feedback + grounded-brief surface 추가
- `docs/PRODUCT_SPEC.md` — 2곳(line 18, 27): Current Product + Product Framing에 response feedback + grounded-brief surface 추가
- `docs/ACCEPTANCE_CRITERIA.md` — 1곳(line 23): "Recent results can show" 앞에 response feedback + grounded-brief trace 출하 사실 2줄 추가
- `docs/TASK_BACKLOG.md` — 1곳(line 5): shipped contract에 response feedback + grounded-brief surface 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 4개 파일의 top-level current product/contract 요약에 shipped surface 2종 누락:
  - response feedback capture
  - grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, artifact-linked reject/reissue reason traces
- 이전 라운드에서 README, project-brief, PRODUCT_PROPOSAL, MILESTONES, NEXT_STEPS 및 instruction docs 동기화 완료
- 근거 앵커: `README.md:57-62`, `docs/PRODUCT_SPEC.md:48-64`

## 핵심 변경
- 4개 파일 top-level 요약에 response feedback + grounded-brief trace/correction surface 추가
- structured correction memory나 durable preference memory 주장 없음
- 기존 스타일/간결성 유지

## 검증
- `git diff --stat` — 4 files changed, 6 insertions(+), 4 deletions(-)
- `rg` — response feedback capture, grounded-brief artifact trace, corrected-save bridge 4개 파일 모두 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 top-level current-summary response-feedback + grounded-brief 동기화 완료
