# entity-card crimson-desert actual-search natural-reload second-follow-up acceptance browser-prefix truth-sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md` (line 1376)

## 사용 skill

- 없음 (docs-only browser-prefix truth-sync)

## 변경 이유

`docs/ACCEPTANCE_CRITERIA.md:1376`이 `entity-card 붉은사막 actual-search 자연어 reload 후 두 번째 follow-up`으로 남아 있어, sibling docs(`README.md:165`)와 test truth(`e2e/tests/web-smoke.spec.mjs:5047`)에 이미 고정된 `browser 자연어 reload` framing과 일치하지 않았습니다.

## 핵심 변경

| 파일 | 변경 |
|---|---|
| ACCEPTANCE_CRITERIA.md:1376 | `actual-search 자연어 reload 후` → `actual-search browser 자연어 reload 후` |

## 검증

- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md` → clean

## 남은 리스크

- 붉은사막 natural-reload docs browser-prefix가 이제 전체 닫혔습니다 (initial + follow-up + second-follow-up, actual-search/noisy-exclusion 포함).
- latest-update natural-reload docs의 동일 패턴은 별도 라운드 대상입니다.
