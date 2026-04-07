# entity-card crimson-desert natural-reload initial milestone/backlog source-path wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 76)
- `docs/TASK_BACKLOG.md` (line 65)

## 사용 skill

- 없음 (docs-only source-path wording clarification)

## 변경 이유

`docs/MILESTONES.md:76`과 `docs/TASK_BACKLOG.md:65`가 `source-path plurality` phrasing과 `, ` separator로 남아 있어, current README/ACCEPTANCE_CRITERIA/test title의 compact `source path(.../provenance)` pattern과 일치하지 않았습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| MILESTONES.md:76 | `source-path plurality` → `source-path`, `, ` → `/` separator |
| TASK_BACKLOG.md:65 | `source-path plurality` → `source-path`, `, ` → `/` separator |

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- crimson-desert natural-reload initial docs가 4개 문서(README, ACCEPTANCE_CRITERIA, MILESTONES, TASK_BACKLOG) 모두 compact source-path pattern으로 정렬됐습니다.
- 다른 family의 `plurality` 또는 `, ` separator 잔여가 있는지 다음 라운드에서 Codex가 확인할 예정입니다.
