# Docs ACCEPTANCE_CRITERIA Playwright core-scenario count and claim-coverage gate inventory truth sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- 없음

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:1322`가 Playwright smoke 시나리오 수를 `17`로 기술하고 있었으나, 실제 Current Gates 항목 수는 `79`임. 또한 claim-coverage gate inventory에 focus-slot reinvestigation explanation (improved/regressed/unchanged) 커버리지가 반영되지 않았음.

## 핵심 변경

### docs/ACCEPTANCE_CRITERIA.md
1. Playwright 시나리오 수: `17 core browser scenarios` → `79 core browser scenarios`
2. Claim-coverage panel gate inventory에 `focus-slot reinvestigation explanation (improved/regressed/unchanged with natural Korean particle normalization)` 추가

## 검증

- `awk` count 검증: Current Gates 항목 79개 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- Current Gates 항목 수는 시나리오 추가 시 수동 동기화 필요.
- 총 Playwright 테스트 수(`82`)와 Current Gates 항목 수(`79`)가 다른 이유는 일부 시나리오가 gate 목록에 개별 항목으로 분리되지 않았기 때문일 수 있으나, 이번 슬라이스에서는 기존 목록 구조를 유지함.
