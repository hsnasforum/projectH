# latest-update mixed-source single-source news-only natural-reload docs-next-steps family-closure truth-sync completion

## 변경 파일
- `docs/NEXT_STEPS.md`

## 사용 skill
- 없음 (handoff 기반 직접 구현)

## 변경 이유
- `docs/NEXT_STEPS.md:16`이 latest-update 3-branch natural-reload family(mixed/single/news-only)의 exact-field, follow-up, second-follow-up closure를 root summary에 반영하지 못함.

## 핵심 변경
- mixed-source: `store.steampowered.com`, `yna.co.kr`, `WEB`, `최신 확인`, `공식+기사 교차 확인`, `보조 기사` · `공식 기반` exact-field/follow-up/second-follow-up continuity 명시
- single-source: `example.com/seoul-weather`, `WEB`, `최신 확인`, `단일 출처 참고`, `보조 출처` 동일
- news-only: `hankyung.com`, `mk.co.kr`, `WEB`, `최신 확인`, `기사 교차 확인`, `보조 기사` 동일

## 검증
- `git diff --check`: clean

## 남은 리스크
- scenario count 73 유지.
