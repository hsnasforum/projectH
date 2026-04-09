# docs: README project-brief PRODUCT_PROPOSAL ARCHITECTURE MILESTONES TASK_BACKLOG top-level next-phase reviewed-memory boundary truth sync

## 변경 파일
- `README.md` — "Next Phase Design Target" 앞에 "Current Reviewed-Memory Boundary" 섹션 추가, Next Phase 문구 수정
- `docs/project-brief.md` — "Next Phase Design Target" 앞에 "Current Reviewed-Memory Boundary" 섹션 추가, Next Phase 문구 수정
- `docs/PRODUCT_PROPOSAL.md` — "Next Phase Design Target" 앞에 "Current Reviewed-Memory Boundary" 섹션 추가, Next Phase Goal 문구 수정
- `docs/ARCHITECTURE.md` — "Next Design Target" 앞에 "Current Reviewed-Memory Boundary" 섹션 추가, Next Design Target 문구 수정
- `docs/MILESTONES.md` — "Next Phase" 앞에 "Current Reviewed-Memory Boundary" 섹션 추가, Next Phase 문구 수정
- `docs/TASK_BACKLOG.md` — "next phase target" 줄 앞에 "current reviewed-memory boundary" 항목 추가, next phase 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 6개 파일이 "correction / approval / preference memory"를 전부 미래 사항으로 프레이밍
- 실제 shipped truth: review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), emitted/apply/result/active-effect path, stop-apply, reversal, conflict-visibility 이미 출하
- broader structured correction memory, durable preference memory, cross-session memory만 실제로 미출하

## 핵심 변경
- 6개 파일 모두에 "Current Reviewed-Memory Boundary" 섹션/항목 추가
- shipped reviewed-memory surface: review queue, aggregate apply trigger, emitted/apply/result/active-effect, stop-apply/reversal/conflict-visibility
- Next Phase / Next Design Target 문구를 "extends the shipped boundary" 패턴으로 수정
- broader structured correction memory, durable preference memory, cross-session memory는 next/later 유지
- structured correction memory나 preference learning 주장 없음

## 검증
- `git diff --stat` — 6 files changed, 31 insertions(+), 9 deletions(-)
- `rg 'Current Reviewed-Memory Boundary|검토 후보|검토 메모 적용'` — 모든 대상 파일 확인
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- AGENTS.md, CLAUDE.md, PROJECT_CUSTOM_INSTRUCTIONS.md의 해당 패턴 잔여 가능 — 현재 scope 외
