# history-card dual-probe mixed-source second-follow-up task-backlog response-origin truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 dual-probe(57번)와 mixed-source(60번) second-follow-up 항목이 exact badge/label drift prevention을 빠뜨려 MILESTONES/README/ACCEPTANCE_CRITERIA보다 약했습니다.

## 핵심 변경
1. 57번: `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention 추가
2. 60번: `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` drift prevention 추가

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
