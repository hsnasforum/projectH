# history-card dual-probe mixed-source initial click-reload task-backlog response-origin truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 dual-probe(29번)와 mixed-source(30번) initial click-reload 항목이 source-path continuity만 적고 response-origin retention을 빠뜨려, MILESTONES/README/ACCEPTANCE_CRITERIA의 current truth보다 약했습니다.

## 핵심 변경
1. 29번: `source-path continuity` → `source-path + response-origin continuity` + `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` 추가
2. 30번: `source-path continuity` → `source-path + response-origin continuity` + `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` 추가

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
