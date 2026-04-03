# 2026-04-03 document-search search-only transcript preview-card first-card ordinal-prefix regression coverage

**범위**: search-only transcript first card의 ordinal prefix 회귀 검증 추가

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오에서 transcript panel first card `.search-preview-name` first에 "1. budget-plan.md" ordinal prefix 포함 assertion 1건 추가

---

## 사용 skill

- `work-log-closeout`

---

## 변경 이유

search-only transcript panel의 first-card는 bare `budget-plan.md`만 잠기고 ordinal prefix `1.`은 잠기지 않았음. response detail panel에서는 이미 first-card `1. budget-plan.md`와 second-card `2. memo.md`로 잠겨 있어, transcript panel의 first-card에도 동일 수준의 ordinal prefix assertion이 필요.

---

## 핵심 변경

1. `e2e/tests/web-smoke.spec.mjs` — search-only 시나리오 transcript panel:
   - `lastAssistant.locator(".search-preview-name").first()` → `toContainText("1. budget-plan.md")` assertion 추가 (line 275)

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `make e2e-test` — 17 passed (2.2m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (server 로직 변경 없음)

---

## 남은 리스크

- smoke 시나리오 수 17 변동 없음
- docs 동기화 불필요
- search-only transcript second-card ordinal prefix 공백 남아 있음. 다음 슬라이스 후보.
- search-plus-summary response detail/transcript both cards ordinal prefix 공백도 남아 있음.
