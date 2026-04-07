# entity-card zero-strong-slot docs-next-steps-task-backlog family truth-sync correction

## 변경 파일
- `docs/NEXT_STEPS.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG 43번이 `follow-up`으로 남아 있었으나 current truth는 `second-follow-up`이고 source-path/WEB badge 누락.
- NEXT_STEPS의 zero-strong-slot summary가 source-path continuity와 full family closure를 빠뜨림.

## 핵심 변경
- TASK_BACKLOG 43번: `follow-up` → `second-follow-up` + `WEB`, `namu.wiki`, `ko.wikipedia.org` 추가
- NEXT_STEPS: `follow-up` → `initial/follow-up/second-follow-up` + `WEB`, `namu.wiki`, `ko.wikipedia.org` source-path continuity 추가

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
