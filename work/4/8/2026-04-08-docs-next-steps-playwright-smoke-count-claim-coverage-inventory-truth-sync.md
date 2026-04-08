# Docs NEXT_STEPS Playwright smoke count and claim-coverage inventory truth sync

## 변경 파일

- `docs/NEXT_STEPS.md`

## 사용 skill

- 없음

## 변경 이유

`docs/NEXT_STEPS.md:16`이 Playwright smoke 시나리오 수를 `75`로 기술하고 있었으나, 실제 현재 count는 `82`임. 또한 claim-coverage focus-slot reinvestigation (improved/regressed/unchanged) smoke 커버리지가 inventory summary에서 누락되어 있었음.

## 핵심 변경

### docs/NEXT_STEPS.md
1. Playwright 시나리오 수: `75` → `82`
2. Claim-coverage panel inventory 설명에 `focus-slot reinvestigation explanation (improved/regressed/unchanged with natural Korean particle normalization)` 추가

## 검증

- `rg -c '^test\(' e2e/tests/web-smoke.spec.mjs`: 82 확인
- `git diff -- docs/NEXT_STEPS.md`: count 및 inventory 변경만 포함
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- `docs/NEXT_STEPS.md`의 inventory 서술은 매 시나리오 추가 시 수동 동기화 필요. 향후 시나리오 추가 시 count와 inventory가 다시 drift할 수 있음.
