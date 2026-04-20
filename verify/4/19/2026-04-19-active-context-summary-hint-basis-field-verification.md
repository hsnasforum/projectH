# 2026-04-19 legacy active-context summary-hint-basis backfill verification

## 변경 파일
- `verify/4/19/2026-04-19-active-context-summary-hint-basis-field-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md`가 missing `active_context.summary_hint_basis` legacy session에 대한 owner-side compatibility backfill, JSON/SQLite parity, focused test/doc sync를 주장하므로 현재 tree와 최소 재검증 결과가 그 설명과 실제로 맞는지 다시 확인해야 했습니다.
- prompt가 기존 same-family verify 경로 `verify/4/19/2026-04-19-active-context-summary-hint-basis-field-verification.md`를 이번 round 출력 위치로 고정했기 때문에, 새 파일을 추가하지 않고 이 경로를 현재 legacy backfill 검수 결과로 in-place 갱신했습니다.
- 이번 verify 후에는 다음 한 슬라이스가 low-confidence였습니다. 이번 round로 user-visible legacy drift는 store/service 경로에서 닫힌 반면, 남은 후보는 same-family proof/canonicalization 보강과 document-first priority reset 사이의 우선순위 판단이라 `.pipeline/gemini_request.md`를 seq 361로 열었습니다.

## 핵심 변경
- latest `/work`의 구현 주장은 현재 코드와 일치합니다.
  - `storage/session_store.py`는 `_compact_summary_hint_for_persist()`와 `_backfill_active_context_summary_hint_basis()`를 실제로 갖고 있고, `_normalize_session()` 말미에서 legacy basis backfill을 호출합니다.
  - `storage/session_store.py::record_correction_for_message()`는 compact helper를 재사용하면서 `active_context["summary_hint_basis"] = "recorded_correction"`를 함께 기록합니다.
  - `storage/sqlite_store.py::_load()`는 JSON owner helper `SessionStore._backfill_active_context_summary_hint_basis()`를 재사용해 SQLite legacy row에도 같은 복구 규칙을 적용합니다.
  - `tests/test_smoke.py`에는 recorded-correction 복구와 no-match fallback regression이 있고, `tests/test_web_app.py`에는 JSON payload 경로와 SQLite backend parity 경로가 모두 추가돼 있습니다.
  - `docs/ACCEPTANCE_CRITERIA.md`와 `docs/ARCHITECTURE.md`는 missing-basis legacy session이 same-session grounded-brief `corrected_text` compact match일 때만 `recorded_correction`으로 backfill되고, 아니면 `current_summary`로 안전 fallback된다고 현재 구현과 맞게 적고 있습니다.
- focused rerun은 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_backfills_recorded_correction tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_without_match_falls_back_to_current_summary tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint` → `Ran 3 tests`, `OK`
  - `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_submit_correction_serializes_active_context_summary_hint_basis` → `Ran 3 tests`, `OK`
  - `python3 -m unittest tests.test_session_store` → `Ran 11 tests`, `OK`
  - `python3 -m py_compile storage/session_store.py storage/sqlite_store.py` → 출력 없음, 통과
  - `git diff --check -- storage/session_store.py storage/sqlite_store.py tests/test_smoke.py tests/test_web_app.py docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md` → 출력 없음, exit code `0`
- 따라서 latest `/work`는 truthful합니다.
  - missing-basis legacy corrected session의 `(현재 요약)` 오라벨 drift를 owner/store/service 경로에서 실제로 닫았고
  - JSON/SQLite payload 경로와 doc sync도 현재 tree에 반영돼 있습니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `storage/session_store.py`, `storage/sqlite_store.py`, `tests/test_smoke.py`, `tests/test_web_app.py`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`, `work/4/19/2026-04-19-legacy-active-context-summary-hint-basis-backfill.md`
  - 결과: `/work`가 설명한 owner-side legacy basis backfill, compact helper 재사용, SQLite shared-helper reuse, focused regression, docs sync가 현재 tree와 일치함을 확인했습니다.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_backfills_recorded_correction tests.test_smoke.SmokeTest.test_legacy_active_context_summary_hint_basis_without_match_falls_back_to_current_summary tests.test_smoke.SmokeTest.test_correction_updates_active_context_summary_hint`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis tests.test_web_app.WebAppServiceTest.test_get_session_payload_backfills_legacy_summary_hint_basis_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_submit_correction_serializes_active_context_summary_hint_basis`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_session_store`
  - 결과: `Ran 11 tests`, `OK`
- `python3 -m py_compile storage/session_store.py storage/sqlite_store.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- storage/session_store.py storage/sqlite_store.py tests/test_smoke.py tests/test_web_app.py docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
  - 결과: 출력 없음, exit code `0`
- Playwright와 broader `tests.test_web_app` full rerun은 이번 verify에서 다시 돌리지 않았습니다.
  - 이유: 이번 round 구현은 browser JS나 copy를 바꾸지 않았고, legacy drift의 핵심 계약은 store/service payload에서 닫혔으므로 focused owner/service regression이 current truth 판정에 충분했습니다.

## 남은 리스크
- 이번 verify는 legacy corrected session 복구를 store/service 경로에서 증명했지만, on-disk legacy session을 브라우저가 실제로 다시 열었을 때 context box가 `(기록된 수정본)`으로 보이는 seeded Playwright 경로는 아직 별도 고정돼 있지 않습니다.
- SQLite 경로의 backfill은 `_load()` 시점 canonicalization입니다. 현재 앱 경로에서는 안전하지만, raw SQLite blob 자체를 eager migration처럼 즉시 rewrite하지는 않으므로 후속 write 전까지 저장값은 legacy shape로 남을 수 있습니다.
- 그래서 next slice는 low-confidence였습니다. same-family로 더 가면 proof/canonicalization 보강 후보가 남고, family를 닫으면 document-first higher-priority slice로 돌아가야 합니다. 이 우선순위는 operator stop 사유가 아니라 arbitration 대상이라 `.pipeline/gemini_request.md` `CONTROL_SEQ: 361`을 열었습니다.
