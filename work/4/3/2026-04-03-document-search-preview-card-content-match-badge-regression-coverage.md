# 2026-04-03 document-search preview-card content-match badge regression coverage

**범위**: second preview card의 `내용 일치` badge path 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 response detail + transcript 양쪽의 second card에 `memo.md` filename과 `내용 일치` badge assertion 추가 (4건)

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

직전 라운드에서 first card의 `파일명 일치` badge는 잠갔지만, second card의 `내용 일치` badge path는 직접 잠그지 않았음. fixture 조합에서 `memo.md`가 content match로 분류되므로 이 branch가 shipped contract이면서도 regression coverage가 없었음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오:
   - response detail: second `.search-preview-name` → "memo.md" 포함, second `.search-preview-match` → "내용 일치" 포함
   - transcript: 동일 2건

---

## 검증

- `make e2e-test` — 17 passed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs는 이미 `파일명 일치 / 내용 일치` 양쪽을 언급하고 있어 추가 동기화 불필요
- preview-card contract(filename, tooltip, badge 양쪽, snippet)의 code/regression/docs가 모두 정합한 상태. same-family current-risk 닫힘.
