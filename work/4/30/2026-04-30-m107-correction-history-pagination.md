# 2026-04-30 M107 correction history pagination

## 변경 파일

- `storage/correction_store.py`
- `app/handlers/corrections.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_summary.py`
- `work/4/30/2026-04-30-m107-correction-history-pagination.md`

## 사용 skill

- `e2e-smoke-triage`: `correction-show-more-btn` 동작이 offset 기반 append로 바뀌는 UI flow 변경임을 확인하고, Playwright는 후속 Axis/CI 범위로 남겼다.
- `finalize-lite`: code-only handoff 검증 범위와 dist/E2E 미실행 리스크를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 `/work` 형식으로 정리했다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1477 / `m107_axis1_correction_history_pagination` 지시에 따라 correction history listing API에 `offset` 파라미터를 추가했다.
- 기존 `correction-show-more-btn`은 limit를 키워 전체를 다시 받는 방식이었으므로, 현재 목록 길이를 offset으로 다음 batch를 받아 append하는 방식으로 바꿨다.

## 핵심 변경

- `CorrectionStore.list_filtered()`에 `offset` 파라미터를 추가하고 정렬 후 `records[offset:offset + limit]` slice를 반환하게 했다.
- `CorrectionHandlerMixin.get_correction_list()`와 `GET /api/corrections/list`에서 `offset`을 수용하고 storage까지 전달하게 했다.
- `fetchCorrectionList()`에 `offset?: number`를 추가하고 URL query로 전달하게 했다.
- `PreferencePanel`의 correction history 목록을 고정 page size 기반으로 조회하고, 더 보기 클릭 시 현재 목록 길이를 offset으로 다음 batch를 append하게 했다.
- 다음 batch가 page size보다 작으면 `correction-show-more-btn`을 숨기도록 `correctionListHasMore` 상태를 추가했다.
- `tests/test_correction_summary.py`에 `test_correction_list_respects_offset`을 추가했다.

## 검증

- `python3 -m py_compile storage/correction_store.py app/handlers/corrections.py app/web.py` 통과.
- `python3 -m unittest -v tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_respects_offset` 통과.
- `python3 -m unittest -v tests.test_correction_summary` 통과.
- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` 통과.
- `git diff --check -- storage/correction_store.py app/handlers/corrections.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_correction_summary.py` 통과.

## 남은 리스크

- handoff 지시에 따라 dist 재빌드는 하지 않았다. `offset` client/UI 변경의 정적 번들 반영은 Axis 2 범위다.
- Playwright는 실행하지 않았다. show-more offset append flow는 후속 E2E slice 또는 CI에서 확인해야 한다.
- docs 동기화는 하지 않았다. 현재 handoff가 code-only이며, 3+ docs-only 규칙상 이후 publish/operator_retriage 번들에서 정리될 수 있다.
- commit, push, PR publish는 implement lane 금지사항에 따라 수행하지 않았다.
