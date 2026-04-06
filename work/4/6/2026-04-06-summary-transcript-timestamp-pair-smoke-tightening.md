# summary transcript timestamp pair smoke tightening

날짜: 2026-04-06

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 133 추가)

## 사용 skill

- 없음 (단일 assertion 추가)

## 변경 이유

- 문서 계약(`README.md`, `docs/ACCEPTANCE_CRITERIA.md`)은 plural `per-message timestamps`를 약속하고 있으나, 직전 슬라이스에서 첫 번째 timestamp만 same-day regex shape로 좁혔고 두 번째 timestamp는 count로만 간접 확인 상태였습니다.
- scenario 1에서 transcript `.message-when` 2건 모두 same-day `오전/오후 HH:MM` shape를 직접 검증하도록 하여 per-message timestamp 계약과 smoke assertion을 완전히 일치시켰습니다.

## 핵심 변경

```diff
  await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
+ await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
  await expect(page.locator('#transcript [data-testid="transcript-meta"]').last()).toContainText("문서 요약");
```

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (4.2m), 전체 green
- `python3 -m unittest -v tests.test_web_app`: test-only Playwright contract tightening 라운드이므로 생략

## 남은 리스크

- `toLocaleTimeString("ko-KR")` locale 환경 의존성은 직전 슬라이스와 동일한 수준이며, 현재 CI 환경에서 안정적으로 통과합니다.
- scenario 1 이외의 scenario에서 timestamp assertion은 아직 broad하지만, 이번 슬라이스 범위 밖입니다.
