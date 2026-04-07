# entity-card dual-probe natural-reload source-path task-backlog exact-url truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 dual-probe natural-reload source-path 2개 항목(47, 49번)이 generic `pearlabyss.com dual-probe URLs`만 적고 exact boardNo URL pair를 빠뜨려 root docs보다 약했습니다.

## 핵심 변경
- 47번: `pearlabyss.com/ko-KR/Board/Detail?_boardNo=200`, `...300` exact URL pair로 변경
- 49번: 동일 exact URL pair로 변경

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
