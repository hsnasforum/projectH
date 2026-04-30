# 2026-04-30 M109 merge gate fix

## 변경 파일

- `storage/sqlite/correction.py`
- `tests/test_correction_summary.py`
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/30/2026-04-30-m109-merge-gate-fix.md`

## 사용 skill

- `github`: PR 상태, stacked base, draft/merge 상태 확인에 사용
- `security-gate`: SQLite 조회/브라우저 smoke/외부 GitHub merge 경계 점검에 사용
- `release-check`: merge 전 검증 범위와 남은 리스크 정리에 사용
- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 결과 정리에 사용

## 변경 이유

- #91~#100이 이미 merged된 상태에서 #101만 남아 있었고, #101 merge 전 Playwright smoke에서 SQLite correction list `offset` 누락과 일부 E2E route mock drift가 확인되었습니다.
- `GET /api/corrections/list?limit=...&offset=...`는 JSON store뿐 아니라 SQLite store에서도 같은 동작을 해야 하므로 merge gate 전에 parity를 보강했습니다.

## 핵심 변경

- `SQLiteCorrectionStore.list_filtered()`에 `offset` 인자를 추가하고 `LIMIT ? OFFSET ?` 쿼리로 적용했습니다.
- SQLite correction list offset 회귀를 잡는 단위 테스트를 추가했습니다.
- query string이 붙은 `/api/corrections/list` 요청도 Playwright route mock이 잡도록 관련 정규식을 보강했습니다.
- correction status filter smoke가 `PreferencePanel`의 빈 선호 조기 상태에 막히지 않도록 anchor preference fixture를 추가했습니다.

## 검증

- `python3 -m py_compile storage/sqlite/correction.py tests/test_correction_summary.py` — PASS
- `python3 -m unittest -v tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_filters_by_status tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_searches_by_query tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_respects_limit tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_respects_offset tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_respects_offset_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_preference_list_respects_limit_and_offset` — PASS
- `cd app/frontend && npx tsc --noEmit` — PASS
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "correction list item click shows correction detail panel|correction history status filter narrows list|correction history show more appends next page|preference show more appends next page|preference search filters preference list|preference delete removes preference from list|preference reliability toggle updates badge|preference text edit updates corrected text|correction history search filters by query" --reporter=line` — PASS, 9 passed
- `git diff --check -- storage/sqlite/correction.py tests/test_correction_summary.py e2e/tests/web-smoke.spec.mjs` — PASS

## 남은 리스크

- 전체 `make e2e-test`와 전체 unittest는 범위 대비 비용이 커서 실행하지 않았습니다.
- #91~#100은 이 세션 중 이미 GitHub에서 merged 상태로 바뀌었으며, #101은 `feat/m96-bundle`로 retarget한 뒤 merge해야 M99~M109 누적분이 최하위 landing branch에 들어갑니다.
