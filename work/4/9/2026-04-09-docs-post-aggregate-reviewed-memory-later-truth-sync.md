# docs: MILESTONES TASK_BACKLOG post-aggregate reviewed-memory later/no-apply truth sync

## 변경 파일
- `docs/TASK_BACKLOG.md` — line 302: "no post-aggregate apply path" → "now shipped"; line 306: "reviewed memory remains later than rollback, disable, conflict, and operator-audit rules" → shipped 항목과 later 항목 분리
- `docs/MILESTONES.md` — line 193: "future reviewed memory remains later than the exact unblock precondition family" → shipped 항목 명시 + rollback/disable/operator-audit만 later로 유지

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- TASK_BACKLOG는 "no post-aggregate apply path"과 "reviewed memory remains later"로 기술하지만, apply/stop-apply/reversal/conflict-visibility는 이미 출하됨
- MILESTONES는 "future reviewed memory remains later"로 전체 reviewed-memory를 미래로 기술하지만, apply 경로는 이미 출하됨
- rollback, disable, operator-audit만 실제로 later

## 핵심 변경
- TASK_BACKLOG 2곳: 출하된 항목과 later 항목 분리
- MILESTONES 1곳: 출하된 항목 명시 + later 항목만 유지

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 기획 문서의 post-aggregate reviewed-memory 출하/later 경계 진실 동기화 완료
