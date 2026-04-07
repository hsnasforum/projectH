# entity-card dual-probe natural-reload source-path milestones-acceptance exact-url truth-sync completion

## 변경 파일
- `docs/MILESTONES.md`
- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- MILESTONES와 ACCEPTANCE_CRITERIA의 dual-probe natural-reload source-path 4개 항목이 generic `pearlabyss.com dual-probe URLs`만 적고 exact boardNo URL pair를 빠뜨려 README/TASK_BACKLOG보다 약했습니다.

## 핵심 변경
- MILESTONES 71번: exact URL pair로 변경
- MILESTONES 73번: exact URL pair로 변경
- ACCEPTANCE_CRITERIA 1362번: exact URL pair로 변경
- ACCEPTANCE_CRITERIA 1364번: exact URL pair로 변경

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
