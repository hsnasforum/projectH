# 2026-04-30 M105 correction history status filter

## 변경 파일

- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_correction_summary.py`
- `work/4/30/2026-04-30-m105-correction-history-status-filter.md`

## 사용 skill

- `finalize-lite`: 구현 라운드 종료 전 검증 범위, 문서 동기화 필요성, `/work` closeout 준비 상태를 점검했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout 형식으로 정리했다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1468 / `m105_axis1_correction_history_status_filter` 지시에 따라 PreferencePanel 교정 이력 목록에 status 필터를 추가했다.
- 백엔드 `get_correction_list(status=...)`와 frontend `fetchCorrectionList({ status })`는 이미 status 파라미터를 지원하므로, UI 연결과 필터 동작 테스트만 좁게 보강했다.

## 핵심 변경

- `PreferencePanel.tsx`에 실제 교정 상태값 기준의 `CorrectionStatusFilter`와 옵션을 추가했다.
- `buildCorrectionListParams`를 통해 `전체` 선택 시 `status` 쿼리를 생략하고, 검색어가 있을 때만 `query`를 전달하게 했다.
- 교정 검색 입력 옆에 `data-testid="correction-status-filter"` select를 추가했다.
- status 필터 변경 시 `fetchCorrectionList`를 즉시 다시 호출하고, 기존 선택된 교정 상세 상태를 초기화하게 했다.
- `tests/test_correction_summary.py`에 `test_correction_list_filters_by_status`를 추가해 `status="confirmed"` 요청이 confirmed 교정만 반환하는지 확인했다.

## 검증

- `app/frontend/node_modules/.bin/tsc --noEmit -p app/frontend/tsconfig.json` 통과.
- `python3 -m unittest -v tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_filters_by_status` 초기 1회 실패: 두 fixture가 같은 delta fingerprint로 묶여 둘 다 confirmed 처리됨.
- `python3 -m unittest -v tests.test_correction_summary.CorrectionSummaryTest.test_correction_list_filters_by_status` fixture 분리 후 통과.
- `python3 -m unittest -v tests.test_correction_summary` 통과.
- `grep -n "correction-status-filter" app/frontend/src/components/PreferencePanel.tsx` 통과.
- `git diff --check -- app/frontend/src/components/PreferencePanel.tsx tests/test_correction_summary.py` 통과.

## 남은 리스크

- handoff 지시에 따라 dist 재빌드는 수행하지 않았다. 정적 번들은 이후 publish/dist slice에서 반영되어야 한다.
- 브라우저 Playwright는 실행하지 않았다. 이번 slice는 frontend source typecheck와 handler-level status filter 테스트로 제한했다.
- 제품 문서 업데이트는 하지 않았다. correction history의 세부 필터 UI 추가이며, 현재 handoff가 code-only 범위로 지정되어 있다.
