# 2026-04-30 M106 correction search expansion

## 변경 파일

- `app/handlers/corrections.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_summary.py`
- `work/4/30/2026-04-30-m106-correction-search-expansion.md`

## 사용 skill

- `e2e-smoke-triage`: UI selector와 교정 이력 flow 변경 범위를 확인하고, Playwright 실제 실행은 Axis 2/CI 범위로 남겼다.
- `finalize-lite`: 코드-only handoff 검증 범위, 미실행 항목, 문서 동기화 리스크를 정리했다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 closeout 형식으로 기록했다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1472 / `m106_axis1_correction_search_expansion` 지시에 따라 correction history의 기존 backend 검색 기능을 UI와 API 경로에 연결했다.
- `get_correction_list`의 기존 기본 `limit=5` 병목을 제거하고, 목록 확장을 위한 `limit` 쿼리 파라미터를 추가했다.

## 핵심 변경

- `CorrectionHandlerMixin.get_correction_list` 기본 `limit`를 `20`으로 올리고, 기존 하드코딩 `5`를 제거했다.
- `GET /api/corrections/list`에서 `limit` 쿼리 파라미터를 파싱해 `query`, `status`와 함께 handler에 전달하게 했다.
- `fetchCorrectionList`에 `limit?: number` 파라미터를 추가하고 URL query로 전달하게 했다.
- `PreferencePanel`에서 검색어/status/limit 변경 시 correction list를 debounce로 재조회하게 했다.
- correction history 목록을 기존 3개 표시에서 API limit 기반 표시로 바꾸고, `data-testid="correction-show-more-btn"` 더 보기 버튼으로 limit를 확장하게 했다.
- `tests/test_correction_summary.py`에 query 검색과 limit 제한 테스트를 추가했다.

## 검증

- `python3 -m py_compile app/handlers/corrections.py app/web.py` 통과.
- `python3 -m unittest -v tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_searches_by_query tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_respects_limit` 통과.
- `python3 -m unittest -v tests.test_correction_summary` 통과.
- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` 통과.
- `git diff --check -- app/handlers/corrections.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_correction_summary.py` 통과.
- `grep -n "correction-search-input" app/frontend/src/components/PreferencePanel.tsx` 통과.

## 남은 리스크

- handoff 지시에 따라 dist 재빌드는 하지 않았다. 정적 번들 반영은 Axis 2 범위다.
- Playwright는 실행하지 않았다. UI selector/flow 추가 검증은 이후 E2E slice 또는 CI에서 확인해야 한다.
- docs 동기화는 하지 않았다. 현재 handoff가 code-only이며, M105와 동일하게 publish/operator_retriage 번들에서 정리될 수 있다.
- commit, push, PR publish는 implement lane 금지사항에 따라 수행하지 않았다.
