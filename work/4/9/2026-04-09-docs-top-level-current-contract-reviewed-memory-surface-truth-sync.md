# docs: README PRODUCT_SPEC ARCHITECTURE MILESTONES project-brief PRODUCT_PROPOSAL top-level current-contract reviewed-memory surface truth sync

## 변경 파일
- `README.md` — 1줄 추가(line 12): Current Shipped Contract에 reviewed-memory surface 추가
- `docs/PRODUCT_SPEC.md` — 2곳(line 18, 27): Current Product + Product Framing에 reviewed-memory slice 추가
- `docs/ARCHITECTURE.md` — 1곳(line 10): Current Contract에 reviewed-memory slice 추가
- `docs/MILESTONES.md` — 1곳(line 6): Current Product에 reviewed-memory slice 추가
- `docs/project-brief.md` — 2곳(line 14, 15): Current Contract 요약 + web shell 상세에 reviewed-memory surface 추가
- `docs/PRODUCT_PROPOSAL.md` — 1곳(line 25): Facts에 reviewed-memory slice 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 7곳의 top-level current-contract/product 요약에 response feedback + grounded-brief trace는 이미 반영되었으나, shipped reviewed-memory slice (review queue, aggregate apply trigger, active-effect path) 누락
- 근거 앵커: `docs/PRODUCT_SPEC.md:58`/`60`/`1520`/`1539`, `docs/ARCHITECTURE.md:15`/`85`

## 핵심 변경
- 6개 파일 7곳에 "first reviewed-memory slice (review queue, aggregate apply trigger, and active-effect path)" 또는 동등한 요약 추가
- broader structured correction memory, durable preference memory 주장 없음
- full lifecycle 상세 반복하지 않음

## 검증
- `git diff --stat` — 6 files changed, 8 insertions(+), 7 deletions(-)
- `rg 'reviewed-memory|검토 후보|aggregate apply trigger'` — 모든 대상 파일 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 top-level current-contract reviewed-memory surface 동기화 완료
