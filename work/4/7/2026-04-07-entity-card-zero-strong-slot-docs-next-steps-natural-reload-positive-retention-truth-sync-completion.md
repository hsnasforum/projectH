# entity-card zero-strong-slot docs-next-steps natural-reload positive-retention truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 zero-strong-slot natural-reload summary가 generic wording만 적고 `WEB`/`설명 카드`/`설명형 단일 출처`/`백과 기반`/`namu.wiki`/`ko.wikipedia.org` positive retention을 빠뜨림.

## 핵심 변경
- exact-field: `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` retention 추가
- follow-up: + source-path continuity + drift prevention 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
