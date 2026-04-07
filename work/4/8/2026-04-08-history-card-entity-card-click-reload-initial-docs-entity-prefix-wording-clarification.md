# history-card entity-card click-reload initial docs entity-prefix wording clarification

## 변경 파일

- `README.md` (line 129)
- `docs/MILESTONES.md` (line 47)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1338)
- `docs/TASK_BACKLOG.md` (line 36)

## 사용 skill

- 없음 (docs-only prefix clarification)

## 변경 이유

history-card entity-card click-reload initial docs 4곳이 `history-card`만 적고 있어, 바로 옆 latest-update sibling line들과 나란히 읽을 때 entity-card 대상임이 덜 직접적이었습니다. follow-up docs는 이전 라운드에서 이미 `history-card entity-card`로 정렬되었으므로, initial docs prefix도 동일하게 맞췄습니다.

## 핵심 변경

4곳 모두 `history-card` → `history-card entity-card` prefix 정렬.

## 검증

- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- click-reload docs set(initial + follow-up)은 이번 라운드로 모두 닫혔습니다.
- 다른 answer-mode family(crimson, entity-card actual-search natural-reload 등)의 별도 패턴은 별도 라운드 대상입니다.
