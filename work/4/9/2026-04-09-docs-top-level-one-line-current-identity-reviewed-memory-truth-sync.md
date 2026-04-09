# docs: top-level one-line current-identity reviewed-memory truth sync

## 변경 파일
- `README.md` — 1곳(line 3): 제품 정의 한 줄에 reviewed-memory slice 추가
- `CLAUDE.md` — 1곳(line 5): Current Identity에 reviewed-memory slice 추가
- `PROJECT_CUSTOM_INSTRUCTIONS.md` — 1곳(line 1): 제품 정의 한 줄에 reviewed-memory slice 추가
- `docs/PRODUCT_SPEC.md` — 1곳(line 6): Current shipped contract에 reviewed-memory slice 추가
- `docs/project-brief.md` — 1곳(line 5): One-Line Current Product Definition에 reviewed-memory slice 추가
- `docs/PRODUCT_PROPOSAL.md` — 2곳(line 6, 16): shipped contract + One-Line Definition에 reviewed-memory slice 추가
- `docs/TASK_BACKLOG.md` — 1곳(line 5): shipped contract에 reviewed-memory slice 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 8곳의 최상위 one-line 제품 정의/상태 문구가 "local-first document assistant web MVP"로만 기술하여 shipped reviewed-memory first slice 누락
- 실제 shipped truth: review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), active-effect path 이미 출하

## 핵심 변경
- 7개 파일 8곳에 "first reviewed-memory slice (review queue, aggregate apply trigger, and active-effect path)" 또는 동등 요약 인라인 추가
- broader structured correction memory, durable preference memory 주장 없음
- full lifecycle 상세 반복하지 않음

## 검증
- `git diff --stat` — 7 files changed, 8 insertions(+), 8 deletions(-)
- `rg 'reviewed-memory slice|review queue.*aggregate apply'` — 모든 대상 파일 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — 전체 repo docs의 top-level one-line current-identity reviewed-memory 동기화 완료
