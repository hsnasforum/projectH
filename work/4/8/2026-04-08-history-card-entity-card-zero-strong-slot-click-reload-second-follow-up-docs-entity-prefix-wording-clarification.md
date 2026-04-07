# history-card entity-card zero-strong-slot click-reload second-follow-up docs entity-prefix wording clarification

## 변경 파일

- `README.md` (line 149)
- `docs/MILESTONES.md` (line 67)
- `docs/ACCEPTANCE_CRITERIA.md` (line 1358)
- `docs/TASK_BACKLOG.md` (line 56)

## 사용 skill

- 없음 (docs-only prefix clarification)

## 변경 이유

zero-strong-slot click-reload second-follow-up docs 4곳이 `entity-card`만 적고 있어, 바로 아래 natural-reload sibling line들과 나란히 읽을 때 click-reload history-card 대상임이 덜 직접적이었��니다. initial/follow-up docs는 이미 `history-card entity-card`로 정렬되었으므로, second-follow-up docs prefix도 동일하게 맞췄습니다.

## 핵심 변경

4곳 모두 `entity-card` → `history-card entity-card` prefix 정렬.

## 검증

- `git diff --check -- README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- zero-strong-slot click-reload docs set(initial + follow-up + second-follow-up) 전체가 이번 라운드로 닫혔습니다.
- zero-strong-slot natural-reload docs prefix와 다른 family의 별도 docs 패턴은 별도 라운드 대상입니다.
