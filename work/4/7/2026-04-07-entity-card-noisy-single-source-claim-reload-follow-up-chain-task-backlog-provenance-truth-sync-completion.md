# entity-card noisy single-source claim reload follow-up-chain task-backlog provenance truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 entity-card noisy single-source claim follow-up chain 4개 항목(76-79번)이 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` positive retention과 `context box` provenance 표기를 빠뜨려 root docs보다 약했습니다.

## 핵심 변경
- 4개 항목 모두 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지 추가
- 4개 항목 모두 `source_paths` → `source_paths/context box` provenance 표기 확장

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
