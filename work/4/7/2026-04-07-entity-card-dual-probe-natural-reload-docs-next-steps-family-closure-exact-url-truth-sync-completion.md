# entity-card dual-probe natural-reload docs-next-steps family-closure exact-url truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 dual-probe natural-reload summary가 generic source-path wording에 머물러 exact boardNo URL pair와 second-follow-up closure를 반영하지 못했습니다.

## 핵심 변경
- dual-probe natural-reload source-path: exact `_boardNo=200`, `_boardNo=300` URL pair 명시
- second-follow-up closure: `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` drift prevention 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
