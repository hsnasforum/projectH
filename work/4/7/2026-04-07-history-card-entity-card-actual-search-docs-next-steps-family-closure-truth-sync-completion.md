# history-card entity-card actual-search docs-next-steps family-closure truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`이 history-card entity-card actual-search click-reload family(initial/follow-up/second-follow-up)를 root summary에 반영하지 않음.

## 핵심 변경
- actual-search click-reload family closure: `namu.wiki`, `ko.wikipedia.org` source-path plurality + `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` continuity 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
