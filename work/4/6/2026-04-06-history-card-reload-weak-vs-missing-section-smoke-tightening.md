# history-card reload weak-vs-missing section smoke tightening

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs` (+7 lines, -2 lines)

## 사용 skill
- 없음

## 변경 이유
- history-card reload scenario의 pre-seeded record가 단순 `summary_text`만 넣고 있어 weak/missing section 분리 유지를 browser-visible smoke에서 검증하지 못했음
- runtime/service contract는 `tests/test_web_app.py:9230-9294`에서 reload 후 weak slot과 missing slot이 분리 유지돼야 한다고 이미 닫혀 있으므로, browser smoke에서도 같은 계약을 잠그는 것이 current-risk reduction

## 핵심 변경
1. pre-seeded record fixture 보강: `summary_text`에 "단일 출처 정보 (교차 확인 부족, 추가 확인 필요):"와 "확인되지 않은 항목:" section header 포함, `claim_coverage`에 weak+missing item 추가
2. reload 후 `response-text`가 두 section header를 실제로 포함하는지 `toContainText` assertion 2건 추가

## 검증
- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: clean
- `make e2e-test`: 17 passed (3.0m)
- `python3 -m unittest -v tests.test_web_app`: 생략 (test-only Playwright tightening, Python 코드 변경 없음)

## 남은 리스크
- claim-coverage와 web-search history badges scenario는 helper/render path로 현재 smoke family 대상이 아님
- pre-seeded record fixture의 weak/missing text는 backend test와 동일한 section header를 사용하지만, runtime이 생성하는 것이 아니라 stored_summary_text를 그대로 재사용하므로, runtime format이 바뀌면 fixture도 함께 갱신해야 함
