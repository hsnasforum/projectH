# docs: TASK_BACKLOG reviewed-memory disable state-machine later wording truth sync

## 변경 파일
- `docs/TASK_BACKLOG.md` — 1곳(line 365): disable state machine later 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 365: "the disable state machine remains later"로 적어 stop-apply lifecycle이 미출하인 것처럼 프레이밍
- 실제 shipped truth: `future_reviewed_memory_stop_apply`는 이미 `record_stage`에서 동작 (`app/handlers/aggregate.py:467`/`470`)
- `docs/ARCHITECTURE.md:1165`에서도 동일하게 이미 수정 완료된 패턴

## 핵심 변경
- TASK_BACKLOG:365 — "the disable contract surface is shipped read-only while the disable state machine remains later" → "the disable contract surface is shipped read-only and the stop-apply lifecycle (`future_reviewed_memory_stop_apply`) is shipped on `record_stage`; per-precondition disable satisfaction booleans remain later"
- disable contract가 read-only라는 보수적 의미 보존
- per-precondition satisfaction booleans later 유지

## 검증
- `git diff -- docs/TASK_BACKLOG.md` — 1줄 변경 확인
- `rg 'disable state machine remains later'` — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — TASK_BACKLOG의 disable state-machine later 진실 동기화 완료
