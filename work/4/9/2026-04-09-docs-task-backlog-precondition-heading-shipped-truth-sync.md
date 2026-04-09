# docs: TASK_BACKLOG remaining reviewed-memory precondition heading shipped-truth bundle

## 변경 파일
- `docs/TASK_BACKLOG.md` — 4곳(line 332, 409, 436, 475): "Fix ..." future-style heading → "Keep the shipped ... fixed ..." 현재형 heading

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 4개 항목 heading이 "Fix ..."로 시작해 아직 미출하 작업처럼 프레이밍됨
- MILESTONES는 이미 "is now fixed" / "are now fixed and shipped"로 수정 완료
- 권위 문서(PRODUCT_SPEC, ARCHITECTURE, ACCEPTANCE_CRITERIA)도 이미 shipped 현재형
- TASK_BACKLOG heading만 잔여 drift 상태

## 핵심 변경
- TASK_BACKLOG:332 — "Fix `reviewed_memory_boundary_defined` to one first narrow reviewed scope only:" → "Keep the shipped `reviewed_memory_boundary_defined` fixed to one narrow reviewed scope:"
- TASK_BACKLOG:409 — "Fix `conflict_visible_reviewed_memory_scope` to one exact same-session visibility boundary only:" → "Keep the shipped ... fixed to one exact same-session visibility boundary:"
- TASK_BACKLOG:436 — "Fix `operator_auditable_reviewed_memory_transition` to one exact local transition-trace contract only:" → "Keep the shipped ... fixed to one exact local transition-trace contract:"
- TASK_BACKLOG:475 — "Fix first same-session unblock semantics as binary and all-required:" → "Keep the shipped same-session unblock semantics fixed as binary and all-required:"

## 검증
- `git diff -- docs/TASK_BACKLOG.md` — 4줄 변경 확인
- `rg` stale "Fix ..." heading 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — TASK_BACKLOG reviewed-memory precondition heading shipped-truth 동기화 완료
