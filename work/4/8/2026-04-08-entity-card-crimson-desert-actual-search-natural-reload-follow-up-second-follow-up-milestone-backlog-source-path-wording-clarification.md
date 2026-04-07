# entity-card crimson-desert actual-search natural-reload follow-up + second-follow-up milestone/backlog source-path wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 77, 85)
- `docs/TASK_BACKLOG.md` (line 66, 74)

## 사용 skill

- 없음 (docs-only source-path wording clarification)

## 변경 이유

crimson-desert actual-search natural-reload follow-up/second-follow-up planning docs 4곳이 `source-path plurality` phrasing과 `, ` separator로 남아 있어, current README/ACCEPTANCE_CRITERIA/test title의 compact `source path(namu.wiki/ko.wikipedia.org)` pattern과 일치하지 않았습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| MILESTONES.md:77 | `source-path plurality` → `source-path`, `and` → `/` separator |
| MILESTONES.md:85 | `, ` → `/` separator (source-path 부분) |
| TASK_BACKLOG.md:66 | `source-path plurality` → `source-path`, `, ` → `/` separator |
| TASK_BACKLOG.md:74 | `, ` → `/` separator (source-path 부분) |

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- crimson-desert actual-search natural-reload follow-up/second-follow-up planning docs가 이번 라운드로 정렬됐습니다.
- 다른 family의 `plurality`/`, ` separator 잔여가 있는지 다음 라운드에서 Codex가 확인할 예정입니다.
