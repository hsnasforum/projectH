# 2026-03-31 uploaded search failure surface verification

## 변경 파일
- `verify/3/31/2026-03-31-uploaded-search-failure-surface-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-uploaded-search-failure-surface.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-reload-answer-mode-operator-approval-record-sync-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 업로드 검색 경로의 silent failure를 user-visible notice로 surface하는 production 변경 1건과 smoke regression 1건만 추가했다고 주장하므로, 이번 검수에서는 그 코드/테스트 존재 여부, current MVP 방향 일탈 여부, 그리고 필요한 최소 회귀만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 production/test 변경 주장은 대부분 현재 코드와 일치합니다.
- `core/agent_loop.py`의 `_search_uploaded_files()`는 이제 `failed_paths`를 별도로 수집해 4번째 반환값으로 내보내고, 호출부는 `failed_uploaded_paths`를 task log detail에 남긴 뒤 `"일부 파일(N건)을 읽지 못해 검색에서 제외되었습니다."` notice를 기존 `search_notice` / `_append_notice()` surface에 붙입니다.
- 이 notice는 search-only 응답에만 붙는 것이 아니라, 업로드 검색 요약 응답과 저장 승인/저장 완료 응답에도 같은 기존 notice surface로 붙습니다. 따라서 이번 round는 내부 trace만이 아니라 user-visible response contract 변경이 맞습니다.
- `tests/test_smoke.py`에는 `test_uploaded_folder_search_surfaces_failed_file_notice`가 실제로 추가되어 있고, 정상 파일 1개 + 실패 파일 1개에서 검색 결과 유지와 실패 건수 notice를 함께 검증합니다.
- 범위는 current projectH의 document-first MVP 안에 있습니다. 업로드 검색의 current-risk reduction이며, web-search-first 확장이나 approval / reviewed-memory widening은 확인되지 않았습니다.
- 다만 latest `/work`의 `docs 변경 없음` closeout은 fully truthful하지 않습니다. 이번 round는 user-visible uploaded-search notice를 새로 열었는데, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md` 어디에도 그 current shipped behavior가 아직 반영되어 있지 않습니다. repo `Document Sync Rules` 기준으로는 최소 docs sync가 따라와야 합니다.
- whole-project audit이 필요한 상황은 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_uploaded_folder_search_surfaces_failed_file_notice tests.test_web_app.WebAppServiceTest.test_handle_chat_search_uploaded_folder_returns_search_results tests.test_web_app.WebAppServiceTest.test_handle_chat_search_uploaded_folder_can_summarize_results`
  - 통과 (`Ran 3 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-uploaded-search-failure-surface.md`
  - `verify/3/31/2026-03-31-reload-answer-mode-operator-approval-record-sync-verification.md`
  - `core/agent_loop.py` (`_search_uploaded_files`, uploaded search notice append path, summary/save response notice reuse 경로)
  - `tests/test_smoke.py`
  - `tests/test_web_app.py` (기존 업로드 검색 경로 회귀 2건)
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`에 uploaded-search partial-failure notice 문구 부재 확인
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `python3 -m unittest -v tests.test_web_app`
  - `make e2e-test`
  - 이유: 이번 변경은 uploaded-search 경로의 service/response notice와 smoke regression 1건이므로, 새 smoke test 1건과 기존 uploaded-search web-app 회귀 2건만으로 직접 영향 범위를 좁게 재검수할 수 있었습니다.

## 남은 리스크
- code/test는 현재 truth와 맞지만 docs sync가 비어 있어 latest `/work` closeout은 아직 완전히 닫히지 않았습니다.
- notice는 count-only surface라 실패 원인이나 개별 파일명은 드러내지 않습니다. 이것은 현재 slice의 범위 제한에는 맞지만, 이후 더 자세한 UX를 열 때는 별도 판단이 필요합니다.
- dirty worktree가 여전히 넓어 다음 라운드도 unrelated 변경을 건드리지 않는 좁은 docs sync가 안전합니다.
