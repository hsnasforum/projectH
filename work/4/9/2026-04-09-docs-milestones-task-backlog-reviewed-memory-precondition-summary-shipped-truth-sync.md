# docs: MILESTONES TASK_BACKLOG reviewed-memory precondition summary shipped-vs-later truth sync

## 변경 파일
- `docs/MILESTONES.md` — 2곳(line 199, 203): shipped apply path 및 boundary draft 현재형 반영
- `docs/TASK_BACKLOG.md` — 5곳(line 115, 306, 350, 365, 380): apply result shipped 반영, rollback/disable contract surface shipped 반영

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 7개 행이 reviewed-memory apply result, rollback/disable contract surface를 "later" 또는 "future-only"로 프레이밍
- apply / stop-apply / reversal / conflict-visibility 모두 이미 출하됨
- rollback/disable/operator-audit contract surface도 read-only로 이미 출하됨 (state machine만 later)
- 권위 문서(PRODUCT_SPEC, ARCHITECTURE, ACCEPTANCE_CRITERIA)는 이미 현재형으로 확인됨

## 핵심 변경
- MILESTONES:199 — "not reviewed-memory apply" → "apply path shipped separately; promotion and cross-session counting remain later"
- MILESTONES:203 — "one later reviewed-memory boundary draft" → "the shipped reviewed-memory boundary draft remains read-only"
- TASK_BACKLOG:115 — "before actual reviewed-memory apply result machinery exists" → "apply result is shipped; per-precondition satisfaction booleans and promotion remain later"
- TASK_BACKLOG:306 — "rollback, disable, and operator-audit rules remain later" → "contract surfaces shipped as read-only while state machines remain later"
- TASK_BACKLOG:350 — "one exact future rollback target only" → "one exact rollback contract surface with shipped target definition"
- TASK_BACKLOG:365 — "disable = later stop-apply machinery" → "disable = stop-apply of applied effect; contract shipped read-only while state machine remains later"
- TASK_BACKLOG:380 — "one exact future stop-apply target only" → "one exact disable contract surface with shipped target definition"

## 검증
- `git diff -- docs/MILESTONES.md docs/TASK_BACKLOG.md` — 7줄 변경 확인
- `rg` 잔여 stale 문구 검색 — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — MILESTONES/TASK_BACKLOG reviewed-memory precondition summary shipped-vs-later 진실 동기화 완료
