# content-verdict transcript timestamp smoke tightening

날짜: 2026-04-06

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (scenario 7, 8에 각 2줄 추가)

## 사용 skill

- 없음 (assertion 추가만)

## 변경 이유

- scenario 1-6에는 이미 transcript timestamp same-day regex shape assertion이 있으나, content-verdict scenario 2건(late-flip-after-save, content-verdict supersession)에는 아직 없었습니다.
- 문서 계약(`per-message timestamps`)과 일치시키기 위해 두 content-verdict scenario 모두에 동일한 `오전/오후 HH:MM` shape assertion을 추가했습니다.
- 두 scenario는 adjacent content-verdict block이며 같은 파일/검증 경로를 공유하므로 하나의 coherent slice로 묶었습니다.

## 핵심 변경

scenario 7 (`원문 저장 후 늦게 내용 거절해도 saved history와 latest verdict가 분리됩니다`):
```diff
  expect(fs.readFileSync(lateFlipNotePath, "utf-8")).toBe(savedBeforeReject);
+ await expect(page.locator("#transcript .message-when").first()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
+ await expect(page.locator("#transcript .message-when").last()).toHaveText(/오[전후]\s\d{1,2}:\d{2}/);
});
```

scenario 8 (`내용 거절은 approval을 유지하고 나중 explicit save로 supersede 됩니다`):
```diff
  expect(fs.existsSync(rejectedVerdictNotePath)).toBeTruthy();
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
- scenario 9 이후의 scenario에서 transcript timestamp assertion은 아직 없지만, 이번 슬라이스 범위 밖입니다.
