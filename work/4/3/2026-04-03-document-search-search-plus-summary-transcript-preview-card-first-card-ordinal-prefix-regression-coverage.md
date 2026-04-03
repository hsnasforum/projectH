# 2026-04-03 document-search search-plus-summary transcript preview-card first-card ordinal-prefix regression coverage

**범위**: search-plus-summary transcript first card의 ordinal prefix 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-plus-summary 시나리오에서 transcript panel first card `.search-preview-name` first에 "1. budget-plan.md" ordinal prefix 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-plus-summary transcript panel의 first-card는 bare `budget-plan.md`만 잠기고 ordinal prefix `1.`은 잠기지 않았음. response detail panel에서는 이미 both cards ordinal prefix가 전부 잠겨 있었고, search-only scenario에서도 모든 panel의 ordinal prefix가 닫혀 있어, search-plus-summary transcript에서도 동일 수준의 ordinal prefix contract를 시작해야 했음.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-plus-summary 시나리오 transcript panel:
   - `lastAssistant.locator(".search-preview-name").first()` → `toContainText("1. budget-plan.md")` assertion 추가 (line 224)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.7m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요
- search-plus-summary transcript second-card ordinal prefix 공백 1곳만 남아 있음. 다음 슬라이스로 닫으면 전체 ordinal prefix family 완전 종결.
