# history-card entity-card zero-strong-slot click-reload-follow-up milestones-task-backlog web-badge-source-path truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/MILESTONES.md:66`의 zero-strong-slot click-reload follow-up line이 `WEB` badge를 직접 적지 않고 있었습니다.
- `docs/TASK_BACKLOG.md:55`는 `WEB` badge와 `namu.wiki`, `ko.wikipedia.org` source-path continuity 둘 다 빠져 있었습니다.
- current truth (`README.md:148`, `docs/ACCEPTANCE_CRITERIA.md:1357`, browser smoke contract)는 `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`를 모두 직접 드러냅니다.

## 핵심 변경
- MILESTONES: follow-up line에 `WEB` badge 추가
- TASK_BACKLOG: follow-up line에 `WEB` badge + `namu.wiki`, `ko.wikipedia.org` source-path 추가, title에 source-path 반영
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`: clean
- README.md:148, ACCEPTANCE_CRITERIA.md:1357과의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, initial/second-follow-up/natural-reload lines 및 다른 family wording 변경 없음)
