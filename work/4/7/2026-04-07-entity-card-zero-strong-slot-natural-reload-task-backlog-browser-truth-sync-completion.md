# entity-card zero-strong-slot natural-reload task-backlog browser truth-sync completion

## 변경 파일
- `docs/TASK_BACKLOG.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- TASK_BACKLOG의 zero-strong-slot natural-reload browser 2개 항목(44-45번)이 generic wording만 적고 exact badge/label/source-path truth를 빠뜨려 root docs보다 약했습니다.

## 핵심 변경
- 44번: `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` exact-field 추가
- 45번: 동일 exact field + `drift prevention` 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
