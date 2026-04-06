# browser-file-picker transcript timestamp smoke tightening

날짜: 2026-04-06

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 186-187 추가)

## 사용 skill

- 없음 (단일 assertion 추가)

## 변경 이유

- 직전 두 슬라이스에서 scenario 1의 transcript timestamp 2건을 same-day regex shape로 좁혔으나, browser-file-picker summary path(scenario 2)는 아직 transcript timestamp를 직접 검증하지 않았습니다.
- 문서 계약(`per-message timestamps`)과 일치시키기 위해 scenario 2에도 동일한 `오전/오후 HH:MM` shape assertion을 추가했습니다.

## 핵심 변경

```diff
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");
+ await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
+ await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});
```

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (4.1m), 전체 green
- `python3 -m unittest -v tests.test_web_app`: test-only Playwright contract tightening 라운드이므로 생략

## 남은 리스크

- `toLocaleTimeString("ko-KR")` locale 환경 의존성은 기존과 동일한 수준입니다.
- scenario 1, 2 이외의 scenario에서 transcript timestamp assertion은 아직 없지만, 이번 슬라이스 범위 밖입니다.
