# entity-card dual-probe natural-reload initial browser-anchor source-path-exact-field wording clarification

날짜: 2026-04-07

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`

## 사용 skill
- 없음 (test-only wording clarification)

## 변경 이유
- dual-probe initial natural-reload browser anchor titles가 generic wording이어서, 이미 검사 중인 `pearlabyss.com/200`/`pearlabyss.com/300` source-path plurality와 `WEB`/`설명 카드`/`설명형 다중 출처 합의`/`공식 기반`·`백과 기반` exact-field contract가 title에서 드러나지 않았습니다.

## 핵심 변경
- source-path anchor (4368): `(pearlabyss.com/200, pearlabyss.com/300)` 추가
- exact-field anchor (4483): `WEB badge, 설명 카드, 설명형 다중 출처 합의, 공식 기반 · 백과 기반` 명시
- session ID 변경 없음, assertion logic 변경 없음, scenario count 75 유지

## 검증
- `npx playwright test -g "entity-card dual-probe 자연어 reload에서"`: 2 passed
- `git diff --check`: clean

## 남은 리스크
- dual-probe follow-up/second-follow-up browser anchors의 동일 wording clarification은 이번 범위 밖
