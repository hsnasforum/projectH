# 2026-04-04 document-summary response-copy success-notice exact-text smoke tightening

**범위**: summary 시나리오의 response-copy success notice assertion을 exact text로 강화

---

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — line 164 assertion 1줄 교체

---

## 사용 skill

- 없음 (handoff 직접 구현)

---

## 변경 이유

기존 smoke는 summary 시나리오의 response-copy success notice를 `toContainText("본문을 복사했습니다.")`로만 확인했기 때문에, notice box에 예상과 다른 추가 텍스트가 섞여도 assertion이 통과할 수 있었습니다.

shipped UI는 `app/static/app.js`의 `renderNotice()`에서 `noticeBox.textContent = message`로 exact text를 렌더링하고, `responseCopyTextButton` click handler는 고정 success string `"본문을 복사했습니다."`를 전달합니다. 따라서 이 contract을 `toHaveText()`로 잠그는 것이 가장 작은 current-risk reduction입니다.

이전 라운드에서 search-only selected-copy success notice는 이미 `toHaveText()`로 닫혔고, 이번 라운드는 같은 copy-success-notice family의 summary scenario 1건을 마저 닫는 마무리입니다.

---

## 핵심 변경

1. `await expect(page.locator("#notice-box")).toContainText("본문을 복사했습니다.")` → `await expect(page.locator("#notice-box")).toHaveText("본문을 복사했습니다.")`
2. 1줄 교체 (net 0)
3. response-copy success notice assertion이 이제 exact (`toHaveText`)
4. clipboard assertion, summary/evidence assertions, docs, runtime behavior 변동 없음
5. scenario count 17 변동 없음

---

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — 통과
- `rg -n '본문을 복사했습니다\.|response-copy-text|notice-box' e2e/tests/web-smoke.spec.mjs` — line 164 `toHaveText()` 확인
- `make e2e-test` — 17/17 통과 (3.2m)
- `python3 -m unittest -v tests.test_web_app` — 미실행 (test-only smoke-tightening 라운드, server 로직 변경 없음)

---

## 남은 리스크

- copy-success-notice family: summary response-copy(이번), search-only selected-copy(이전) 모두 `toHaveText()`로 닫힘
- 다른 `#notice-box` assertion들은 여전히 `toContainText()` — 별도 family/별도 슬라이스
- smoke 시나리오 수 17 변동 없음
- unrelated dirty worktree는 이번 라운드에서 건드리지 않음
