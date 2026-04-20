# 2026-04-19 active-context summary-hint basis field

## 변경 파일
- `storage/session_store.py`
- `core/agent_loop.py`
- `app/serializers.py`
- `app/static/app.js`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/19/2026-04-19-active-context-summary-hint-basis-field.md`

## 사용 skill
- `doc-sync`: 세션/스키마 + 브라우저 계약 변경을 README / PRODUCT_SPEC / ARCHITECTURE / ACCEPTANCE_CRITERIA와 좁게 동기화하기 위해 사용했습니다.
- `work-log-closeout`: 이번 grounded-brief follow-up-basis field 라운드의 `/work` closeout을 repo 규약 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 이전 라운드(`work/4/19/2026-04-19-grounded-brief-follow-up-basis-browser-surface.md`)에서 `#context-text`가 `active_context.summary_hint`를 `(기록된 수정본)` / `(현재 요약)` 라벨로 구분해 보여 줬지만, 실제 basis 판정은 브라우저 쪽 `compactSummaryHintForBasis()`가 storage-side `" ".join(text.split())` + 240자 cap을 그대로 복제해 추론하는 heuristic이었습니다.
- storage 또는 localization 쪽 compact 규칙이 바뀌면 같은 corrected basis가 `(현재 요약)`으로 잘못 떨어질 수 있었고, same-family next current-risk owner는 이 basis의 truth 위치 자체였습니다.
- 또한 기존 focused browser smoke는 correction helper copy와 context-box basis surface만 고정했고, correction 이후 실제 composer follow-up 한 번이 recorded-correction basis로 이어지는지까지 브라우저 경로에서 닫지 못했습니다.
- 이번 라운드는 basis truth를 active-context owner로 옮기고 실제 follow-up 경로를 같이 pin하는 bounded bundle로 닫았습니다.
- 이번 라운드는 session/schema truth + browser proof 둘 다 바꿉니다 (데이터 필드와 UI 렌더링이 함께 옮겨졌습니다).

## 핵심 변경
- `core/agent_loop.py::_build_active_context()`가 새로 `"summary_hint_basis": "current_summary"`를 함께 돌려주도록 해, document/search/web active-context 모두 생성 시 기준이 `current_summary`로 seed됩니다. 같은 agent의 `_public_active_context()`도 fallback `current_summary`로 basis를 노출하도록 넓혔습니다.
- `storage/session_store.py::record_correction_for_message()`가 기존 summary_hint 재작성 로직 옆에 `active_context["summary_hint_basis"] = "recorded_correction"`를 같이 set하도록 바꿨습니다. SQLite store는 동일 헬퍼를 재사용하므로 JSON / SQLite parity가 보존됩니다.
- `app/serializers.py::_serialize_active_context()`에 `summary_hint_basis` 직렬화를 추가해, `current_summary` / `recorded_correction` 이외 값이면 `current_summary`로 떨어지는 whitelist를 걸었습니다.
- `app/static/app.js`:
  - `compactSummaryHintForBasis()`와 관련 text 비교 heuristic을 제거했습니다.
  - `renderContext()`는 이제 `context.summary_hint_basis === "recorded_correction"`일 때만 `후속 질문 / 재요약 기준 (기록된 수정본):` 라벨을 붙이고, 그 외에는 `(현재 요약):`으로 떨어집니다. 사용자-가시 라벨과 correction helper copy는 바꾸지 않았습니다.
- 테스트:
  - `tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint`에 `summary_hint_basis`가 `current_summary` → `recorded_correction`으로 넘어가는지 직접 고정했습니다.
  - `tests.test_web_app.WebAppServiceTest.test_submit_correction_serializes_active_context_summary_hint_basis`를 추가해, `submit_correction` payload와 이어지는 `get_session_payload`가 모두 `summary_hint_basis = recorded_correction`을 직렬화하는지 고정했습니다.
  - `e2e/tests/web-smoke.spec.mjs`의 `corrected follow-up basis…` 시나리오를 연장해, 수정본 기록 후 request_mode를 `chat`으로 바꿔 `#user-text`로 실제 같은 세션 follow-up을 보내고, 응답 이후에도 `#context-text`가 `후속 질문 / 재요약 기준 (기록된 수정본):` 라벨과 수정본 본문을 유지하는지 직접 고정했습니다.
- 문서: `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`가 이제 `active_context`에 `summary_hint_basis = current_summary | recorded_correction`이 들어가 있으며 correction submit이 그 값을 `recorded_correction`으로 뒤집는다는 계약을 명시적으로 적고 있습니다. 브라우저가 basis를 문자열 모양으로 추론하지 않는다는 점도 적었습니다. memory scope나 durable cross-session 재사용은 손대지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_submit_correction_serializes_active_context_summary_hint_basis`
  - 결과: `Ran 1 test`, `OK` (두 테스트를 같이 실행한 `Ran 2 tests ... OK` 상태에서 확인)
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected.*follow-up basis|follow-up basis.*corrected|수정본.*후속" --reporter=line`
  - 결과: `1 passed (15.0s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "corrected-save" --reporter=line` (follow-up-basis suffix 변경으로 기존 scenario가 깨지지 않았는지 재확인)
  - 결과: `2 passed (38.1s)`
- `python3 -m unittest tests.test_session_store` (storage round-trip 회귀 확인)
  - 결과: `Ran 11 tests`, `OK`
- `python3 -m py_compile storage/session_store.py storage/sqlite_store.py app/serializers.py core/agent_loop.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- storage/session_store.py storage/sqlite_store.py app/serializers.py core/agent_loop.py app/static/app.js tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, exit code `0`
- 이번 라운드는 active-context basis field 이전 + 실제 follow-up browser proof 추가라 좁은 Playwright 재실행으로 충분했고, `make e2e-test` full suite는 과하다고 판단해 생략했습니다.

## 남은 리스크
- 이전 세션에서 이미 disk/SQLite에 저장된 `active_context` 블롭에는 `summary_hint_basis`가 없을 수 있습니다. 그런 세션은 serializer whitelist 덕분에 `current_summary`로 떨어지므로 브라우저도 `(현재 요약)` 라벨을 안전하게 보여 주지만, 직전에 기록된 수정본이 이미 있었다면 같은 세션이 다음 correction 전까지는 `recorded_correction` 라벨로 복원되지 않습니다. 새 correction이나 새 summary 요청이 한 번 들어오면 현재 contract로 돌아옵니다.
- `summary_hint`와 `summary_hint_basis`는 서로 다른 helper에서 쓰이므로 이후 누군가 `summary_hint`만 바꾸고 basis를 갱신하지 않는 새 경로를 추가하면 다시 miscategorize가 생길 수 있습니다. 이런 종류의 drift는 storage `record_correction_for_message()`가 owner인 지금 구조에서 쉽게 좁힐 수 있습니다.
- current tree에는 watcher/runtime/controller/cozy/docs 쪽 broad dirty worktree가 여전히 남아 있으므로, 다음 커밋/리뷰에서는 이번 라운드 대상 파일만 분리해서 보는 편이 안전합니다.
