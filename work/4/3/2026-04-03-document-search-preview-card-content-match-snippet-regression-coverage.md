# 2026-04-03 document-search preview-card content-match snippet regression coverage

**범위**: second preview card의 content-match snippet visibility 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail + transcript 양쪽의 second card에 `.search-preview-snippet` visibility 및 "budget" 텍스트 포함 assertion 추가 (4건)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 second card의 `내용 일치` badge는 잠갔지만, content-match branch의 snippet visibility는 직접 잠그지 않았음. 구현은 `if (sr.snippet)` 조건으로 snippet을 렌더링하므로 이 path도 shipped contract이면서 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오:
   - response detail: second `.search-preview-snippet` → visible + "budget" 텍스트 포함
   - transcript: 동일 2건

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs는 이미 snippet visibility를 언급하고 있어 추가 동기화 불필요
- preview-card contract(filename, tooltip, badge 양쪽, snippet 양쪽)의 code/regression/docs가 모두 정합한 상태. same-family current-risk 닫힘.
