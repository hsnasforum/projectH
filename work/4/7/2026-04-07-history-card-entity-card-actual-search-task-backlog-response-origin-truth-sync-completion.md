# history-card entity-card actual-search task-backlog response-origin truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 actual-search reload family 3개 항목(54-56번)이 source-path plurality만 적고 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` response-origin continuity를 빠뜨려 root docs보다 약했습니다.

## 핵심 변경
- 54번: `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` 추가
- 55번: 동일 + `drift prevention` 명시
- 56번: 동일 + `drift prevention` 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
