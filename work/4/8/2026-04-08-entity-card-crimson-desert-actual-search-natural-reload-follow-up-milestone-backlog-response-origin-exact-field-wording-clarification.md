# entity-card crimson-desert actual-search natural-reload follow-up milestone/backlog response-origin exact-field wording clarification

## 변경 파일

- `docs/MILESTONES.md` (line 75)
- `docs/TASK_BACKLOG.md` (line 64)

## 사용 skill

- 없음 (docs-only response-origin exact-field wording clarification)

## 변경 이유

crimson-desert actual-search natural-reload follow-up planning docs 2곳이 source-path를 포함하지 않고 generic `response-origin continuity`/`truth-sync` framing만 남아 있어, same-family second-follow-up sibling과 current README/ACCEPTANCE_CRITERIA/test title의 combined source-path + response-origin pattern과 일치하지 않았습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| MILESTONES.md:75 | `response-origin continuity` → `source-path + response-origin continuity` + `namu.wiki`/`ko.wikipedia.org` source-path 추가 |
| TASK_BACKLOG.md:64 | `response-origin truth-sync` → `source-path + response-origin continuity` + `namu.wiki`/`ko.wikipedia.org` source-path 추가 |

## 검증

- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md` → clean

## 남은 리스크

- crimson-desert actual-search natural-reload follow-up/second-follow-up planning docs가 source-path + response-origin 모두 정렬됐습니다.
- 다른 family의 `truth-sync` framing 잔여나 source-path 누락은 다음 라운드에서 Codex가 확인할 예정입니다.
