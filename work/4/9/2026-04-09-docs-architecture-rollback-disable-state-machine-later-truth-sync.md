# docs: ARCHITECTURE reviewed-memory rollback-disable state-machine later wording truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 2곳(line 1165, 1166): rollback/disable state machine 부재 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 1165: "no disable state machine or disable satisfaction booleans yet"로 적어 stop-apply lifecycle이 미출하인 것처럼 프레이밍
- line 1166: "no rollback state machine or rollback satisfaction booleans yet"로 적어 reversal lifecycle이 미출하인 것처럼 프레이밍
- 실제 shipped truth: `future_reviewed_memory_stop_apply`와 `future_reviewed_memory_reversal`은 이미 구현되어 `record_stage`에서 `stopped` → `reversed` 전이가 동작
- line 1162와 1164에서 이미 같은 파일 내에서 stop-apply/reversal 출하를 기술하므로 1165-1166과 직접 모순
- per-precondition satisfaction booleans만 실제로 later

## 핵심 변경
- ARCHITECTURE:1165 — "no disable state machine or disable satisfaction booleans yet" → "disable contract stays read-only; stop-apply lifecycle (`future_reviewed_memory_stop_apply`) is shipped on `record_stage`; per-precondition disable satisfaction booleans remain later"
- ARCHITECTURE:1166 — "no rollback state machine or rollback satisfaction booleans yet" → "rollback contract stays read-only; reversal lifecycle (`future_reviewed_memory_reversal`) is shipped on `record_stage`; per-precondition rollback satisfaction booleans remain later"
- contract objects가 read-only라는 보수적 의미 보존
- per-precondition satisfaction booleans later 유지

## 검증
- `git diff -- docs/ARCHITECTURE.md` — 2줄 변경 확인
- `rg` stale 문구 검색 — "no disable/rollback state machine" 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — ARCHITECTURE의 rollback/disable state-machine later 진실 동기화 완료
