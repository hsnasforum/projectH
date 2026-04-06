# history-card reload stored summary text smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+2 lines, 빈 줄 포함)

## 사용 skill
- 없음 (단일 파일 1줄 assertion + 1줄 빈 줄 추가)

## 변경 이유
- history-card reload scenario는 pre-seeded record에 `summary_text: "웹 검색 요약: 붉은사막"`를 넣고 있으나, reload 후 response body가 그 stored text를 실제로 포함하는지 assert하지 않았음
- runtime/service contract는 `tests/test_web_app.py:14650-14742`에서 이미 `load_web_search_record_id` reload가 stored `summary_text`를 재사용해야 한다고 닫혀 있으므로, browser-visible smoke에서도 같은 계약을 잠그는 것이 current-risk reduction

## 핵심 변경
- `e2e/tests/web-smoke.spec.mjs` history-card reload scenario에서 origin detail assertion 이후, timestamp assertion 이전에 `response-text`가 `"웹 검색 요약: 붉은사막"`을 포함하는지 `toContainText` assertion 1건 추가

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (3.0m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- claim-coverage와 web-search history badges scenario는 helper/render path로 transcript message path와 다르며, 현재 timestamp smoke family의 대상이 아님
- history-card reload scenario의 response body continuity는 이번 라운드로 잠김
