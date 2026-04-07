# entity-card dual-probe docs-next-steps natural-reload exact-field-follow-up truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`의 dual-probe natural-reload exact-field/follow-up이 positive retention을 빠뜨림.

## 핵심 변경
- exact-field: `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `공식 기반` · `백과 기반` retention 추가
- follow-up response-origin: 동일 + drift prevention 명시

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
