# entity-card zero-strong-slot click-reload second-follow-up milestones web-badge truth-sync completion

날짜: 2026-04-07

## 변경 파일
- `docs/MILESTONES.md`

## 사용 skill
- 없음 (docs-only truth-sync correction)

## 변경 이유
- `docs/MILESTONES.md:67`의 zero-strong-slot click-reload second-follow-up line이 `WEB` badge를 직접 적지 않고 있었습니다.
- current truth (`README.md:149`, `docs/ACCEPTANCE_CRITERIA.md:1358`, `docs/TASK_BACKLOG.md:56`, browser smoke contract)는 `WEB` badge, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`를 모두 직접 드러냅니다.

## 핵심 변경
- MILESTONES second-follow-up line에 `WEB` badge 추가
- 기존 `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` drift prevention wording 유지
- scenario count `73` 유지

## 검증
- `git diff --check -- docs/MILESTONES.md`: clean
- README.md:149, ACCEPTANCE_CRITERIA.md:1358, TASK_BACKLOG.md:56과의 cross-doc consistency 확인 완료

## 남은 리스크
- 없음 (docs-only correction, 다른 family/line 변경 없음)
