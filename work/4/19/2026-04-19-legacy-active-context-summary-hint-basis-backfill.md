# 2026-04-19 legacy active-context summary-hint-basis backfill

## 변경 파일
- `storage/session_store.py`
- `storage/sqlite_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md`

## 사용 skill
- `doc-sync`: `summary_hint_basis` 호환성 backfill 계약을 field-shape 문서(`docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`)와 좁게 동기화하기 위해 사용했습니다.
- `work-log-closeout`: 이번 legacy active-context basis backfill 라운드의 `/work` closeout을 repo 규약 형식으로 남기기 위해 사용했습니다.

## 변경 이유
- 이전 라운드(`work/4/19/2026-04-19-active-context-summary-hint-basis-field.md`)에서 `summary_hint_basis`를 active-context owner 쪽으로 옮겼지만, 필드가 생기기 전에 저장된 기존 세션은 `summary_hint_basis`가 없어 serializer whitelist 덕에 일단 `current_summary`로 떨어졌습니다. 그래서 이미 recorded correction을 가진 older session은 새 correction이나 새 summary 요청이 다시 들어오기 전까지 `(기록된 수정본)` 라벨이 복원되지 않는 shipped-contract drift가 남아 있었습니다.
- 이번 라운드는 browser-side heuristic을 되살리지 않고, active-context/session owner 쪽에 좁은 호환성 backfill을 하나 더해 legacy data에서도 올바른 basis를 회복하도록 닫았습니다.
- 이번 라운드는 **compatibility behavior만** 바꿉니다. 사용자 눈에 보이는 브라우저 copy나 approval 동작은 바꾸지 않았습니다. 다만 이전에 `(현재 요약)`으로 잘못 라벨링되던 legacy 세션은 이제 조건이 맞으면 `(기록된 수정본)`으로 올바르게 라벨링됩니다.

## 핵심 변경
- `storage/session_store.py`에 공유 static helper 두 개를 추가했습니다.
  - `_compact_summary_hint_for_persist(text, max_chars=240)`: 기존 `record_correction_for_message()` 안의 `" ".join(text.split())` + 240자 cap + `...` 규칙을 단일 헬퍼로 뽑았습니다. 같은 함수 안에서 이 헬퍼를 재사용해 drift 가능성을 줄였습니다.
  - `_backfill_active_context_summary_hint_basis(data)`: 세션 dict를 in-place로 받아 `active_context.summary_hint`가 있는데 `summary_hint_basis`가 whitelisted 값이 아닌 legacy 경우에만 작동합니다. 같은 세션의 grounded-brief assistant 메시지 중 `corrected_text`를 위 compact 헬퍼로 정규화해 현재 `summary_hint`와 동일한 항목이 있으면 `recorded_correction`, 아니면 안전한 fallback `current_summary`를 기록합니다.
- `SessionStore._normalize_session()` 끝부분에서 이 backfill을 호출하도록 해, JSON 백엔드는 `get_session` 경로에서 자동으로 올바른 basis를 반환합니다. 변경이 있으면 기존 normalization이 이어지는 `_save`에서 자연스럽게 영구화됩니다.
- `storage/sqlite_store.py::_load()`에서 raw 세션 dict를 읽은 뒤 같은 helper를 지연 import로 불러 in-memory 백필을 붙였습니다. SQLite 백엔드는 JSON 백엔드와 동일한 owner helper를 재사용하며 divergent SQLite-only 로직은 추가하지 않았습니다.
- browser/heuristic 쪽은 손대지 않았습니다. 라벨링은 여전히 `app/static/app.js::renderContext()`가 serializer가 내려준 `summary_hint_basis`만 보고 결정합니다.
- 테스트 추가:
  - `tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_backfills_recorded_correction`: raw legacy JSON 세션 파일(필드 없음)을 디스크에 직접 쓰고, `SessionStore.get_active_context()`와 `get_session()`이 모두 `recorded_correction`으로 복원하는지 고정했습니다.
  - `tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_without_match_falls_back_to_current_summary`: 매칭되는 correction이 없으면 안전하게 `current_summary`로 떨어지는지 고정했습니다.
  - `tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis`: JSON 백엔드 payload 경로에서 같은 계약을 고정했습니다. 공용 payload 헬퍼 `_legacy_session_payload_missing_basis`는 SQLite 케이스와 공유합니다.
  - `tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis_with_sqlite_backend`: `storage_backend="sqlite"` 설정으로 DB를 만들고, 같은 legacy blob을 raw SQLite INSERT로 직접 넣은 뒤 `service.get_session_payload()`가 SQLite 경로에서도 `recorded_correction`으로 회복되는지 고정했습니다.
- 문서: `docs/ACCEPTANCE_CRITERIA.md`와 `docs/ARCHITECTURE.md`의 `active_context` 필드 설명에 legacy backfill 규칙을 한 줄씩 좁게 추가했습니다. `README.md`와 `docs/PRODUCT_SPEC.md`는 이미 `summary_hint_basis` 계약을 적고 있고 이번 라운드가 user-visible copy를 바꾸지 않았기 때문에 건드리지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_backfills_recorded_correction`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis`
  - 결과: `Ran 1 test`, `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis_with_sqlite_backend`
  - 결과: `Ran 1 test`, `OK` (같이 돌린 4개 세트 `Ran 4 tests ... OK`에서도 동일하게 통과)
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_without_match_falls_back_to_current_summary`
  - 결과: `Ran 1 test`, `OK`
- 기존 basis/correction 회귀 확인: `tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint`, `tests.test_web_app.WebAppServiceTest.test_submit_correction_serializes_active_context_summary_hint_basis`, `tests.test_web_app.WebAppServiceTest.test_get_session_payload_works_with_sqlite_backend`, `tests.test_web_app.WebAppServiceTest.test_submit_correction_updates_grounded_brief_source_message_and_logs` 모두 통과
- `python3 -m unittest tests.test_session_store`
  - 결과: `Ran 11 tests`, `OK`
- `python3 -m py_compile storage/session_store.py storage/sqlite_store.py app/serializers.py core/agent_loop.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- storage/session_store.py storage/sqlite_store.py app/serializers.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: 출력 없음, exit code `0`
- Playwright rerun은 이번 round 구현이 브라우저에 새 copy나 새 surface를 추가하지 않아서 handoff 규약에 따라 생략했습니다.

## 남은 리스크
- backfill은 `corrected_text`와 `summary_hint`의 compact 일치 여부를 owner에서 판정하기 때문에, 만약 수정본이 저장된 뒤 누군가 수동으로 `summary_hint`만 덮어써 두 값이 벌어진 legacy 세션이 있다면 (realistic하지 않지만) `current_summary`로 안전 fallback됩니다. 사용자는 다음 correction/summary 한 번으로 정상 계약으로 돌아옵니다.
- compat 로직이 같은 세션 안에서 여러 번의 correction을 거친 경우에도 correct text 중 하나만 현재 hint와 match하면 `recorded_correction`로 떨어집니다. 이는 latest-hint-wins semantics와 일치하므로 안전합니다.
- current tree에는 watcher/runtime/controller/cozy/docs 쪽 broad dirty worktree가 여전히 남아 있으므로, 다음 커밋/리뷰에서는 이번 라운드 대상 파일(`storage/session_store.py`, `storage/sqlite_store.py`, `tests/test_smoke.py`, `tests/test_web_app.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, 이 `/work` 파일)만 분리해서 보는 편이 안전합니다.
