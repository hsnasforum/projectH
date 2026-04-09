# docs: ARCHITECTURE reviewed-memory recurrence-key practical-next-path truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 1곳(line 703): recurrence-key practical-next-path 문구 수정

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- line 703: "without opening any apply / rollback or user-level-memory layer yet"로 적어 shipped apply/stop-apply/reversal/conflict-visibility lifecycle을 미출하로 프레이밍
- 실제 shipped truth: reviewed-memory apply / stop-apply / reversal / conflict-visibility가 aggregate path 위에서 이미 출하
- user-level memory만 실제로 later

## 핵심 변경
- ARCHITECTURE:703 — "without opening any apply / rollback or user-level-memory layer yet" → "the reviewed-memory apply / stop-apply / reversal / conflict-visibility lifecycle is now also shipped above the aggregate path; user-level memory still remains later"

## 검증
- `git diff -- docs/ARCHITECTURE.md` — 1줄 변경 확인
- `rg 'without opening any apply / rollback'` — 0건
- `git diff --check` — 공백 오류 없음
- 코드, 테스트, 런타임 변경 없음

## 남은 리스크
- 없음 — ARCHITECTURE의 recurrence-key practical-next-path 진실 동기화 완료
