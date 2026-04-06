# summary transcript timestamp format smoke tightening

날짜: 2026-04-06

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 132)

## 사용 skill

- 없음 (단일 assertion 교체)

## 변경 이유

- scenario 1 transcript timestamp assertion이 `not.toBeEmpty()`로만 확인되어, 실제 shipped timestamp format(`오전/오후 HH:MM`)과 무관한 broad gate였습니다.
- `README.md`와 `docs/ACCEPTANCE_CRITERIA.md`는 per-message timestamp contract를 이미 약속하고 있으므로, smoke가 실제 format shape를 잡아야 계약과 일치합니다.
- `app/static/app.js:172-183`의 `formatMessageWhen()`이 same-day일 때 `toLocaleTimeString("ko-KR", { hour: "2-digit", minute: "2-digit" })`를 반환하므로 `오전/오후 HH:MM` regex로 좁혔습니다.

## 핵심 변경

```diff
- await expect(page.locator("#transcript .message-when").first()).not.toBeEmpty();
+ await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
```

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (3.8m), 전체 green
- `python3 -m unittest -v tests.test_web_app`: test-only Playwright contract tightening 라운드이므로 생략

## 남은 리스크

- `toLocaleTimeString("ko-KR")` 출력은 locale 환경에 따라 미세한 formatting 차이가 있을 수 있으나, Playwright CI 환경이 현재 ko-KR locale과 동일하게 동작하고 있어 실질적 위험은 낮습니다.
- 다른 scenario의 timestamp assertion은 아직 broad하지만, 이번 슬라이스 범위 밖입니다.
