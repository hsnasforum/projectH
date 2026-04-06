# search-only transcript timestamp smoke tightening

날짜: 2026-04-06

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 307-308 추가)

## 사용 skill

- 없음 (단일 assertion 추가)

## 변경 이유

- scenario 1, 2, 3에는 이미 transcript timestamp same-day regex shape assertion이 있으나, search-only scenario(scenario 4)에는 아직 없었습니다.
- 문서 계약(`per-message timestamps`)과 일치시키기 위해 scenario 4에도 동일한 `오전/오후 HH:MM` shape assertion을 추가했습니다.
- search-only scenario는 search-only 후 search-plus-summary recovery까지 진행하므로, recovery 후 시점에서 first/last timestamp를 검증합니다.

## 핵심 변경

```diff
  await expect(page.getByTestId("response-search-preview")).toBeVisible();
+ await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
+ await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});
```

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (3.9m), 전체 green
- `python3 -m unittest -v tests.test_web_app`: test-only Playwright contract tightening 라운드이므로 생략

## 남은 리스크

- `toLocaleTimeString("ko-KR")` locale 환경 의존성은 기존과 동일한 수준입니다.
- scenario 5 이후의 scenario에서 transcript timestamp assertion은 아직 없지만, 이번 슬라이스 범위 밖입니다.
