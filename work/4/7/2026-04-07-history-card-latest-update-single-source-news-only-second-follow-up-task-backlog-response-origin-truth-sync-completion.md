# history-card latest-update single-source news-only second-follow-up task-backlog response-origin truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 single-source(61번)와 news-only(62번) second-follow-up 항목이 `WEB` badge와 `최신 확인` answer-mode continuity를 빠뜨려 MILESTONES/README/ACCEPTANCE_CRITERIA보다 약했습니다.

## 핵심 변경
1. 61번: `WEB` badge, `최신 확인` drift prevention 추가
2. 62번: `WEB` badge, `최신 확인` drift prevention 추가

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
