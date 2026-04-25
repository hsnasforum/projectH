STATUS: verified
CONTROL_SEQ: 127
BASED_ON_WORK: work/4/24/2026-04-24-adopted-correction-preference-bridge.md
VERIFIED_BY: Claude
NEXT_CONTROL: .pipeline/implement_handoff.md CONTROL_SEQ 128 (M29 Axis 2: sync count UI + button)

---

## M29 Axis 1 — Adopted Correction → Preference Candidate Bridge

### Verdict

PASS. `app/handlers/preferences.py` + `app/web.py` + `tests/test_preference_handler.py` 변경이 `/work` 기술과 일치하고, 재검증 통과.

### Checks Rerun

- `python3 -m py_compile app/handlers/preferences.py app/web.py` → OK
- `python3 -m unittest tests.test_preference_handler` → `Ran 11 tests in 0.001s`, OK
- `rg -n "sync-adopted-to-candidates|sync_adopted_corrections_to_candidates" app/web.py app/handlers/preferences.py tests/test_preference_handler.py` → 3파일 모두 매칭
- `git diff --check` → OK (출력 없음)

### Implementation Confirmed

- `app/handlers/preferences.py:186`: `sync_adopted_corrections_to_candidates()` — `find_adopted_corrections()` → fingerprint 중복 체크 → `record_reviewed_candidate_preference()` 매핑 → `{"ok": True, "synced_count": N, "skipped_count": M}` 반환 확인
- `app/web.py:396,405-406`: `POST /api/corrections/sync-adopted-to-candidates` 등록 및 `service.sync_adopted_corrections_to_candidates()` 호출 확인
- `tests/test_preference_handler.py:243,281,308`: mapping, skip-existing-fingerprint, empty-adopted-list 3개 테스트 추가 확인

### Field Mapping Verified (preferences.py:200–206)

| Correction 필드 | Preference 인자 |
|---|---|
| `delta_fingerprint` | `delta_fingerprint` |
| `pattern_family` (fallback: CORRECTION_REWRITE) | `candidate_family` |
| `delta_summary` or `corrected_text` | `description` |
| `correction_id` + location info | `source_refs` |
| `original_text` | `original_snippet` |
| `corrected_text` | `corrected_snippet` |

### Discrepancy: handoff file path vs actual

handoff는 `web_app.py`를 언급했으나 이 repo의 실제 HTTP 소유자는 `app/web.py`. `/work` 노트가 이 차이를 명시했고, `app/web.py` 기준으로 검증 완료. 기능 동작에는 영향 없음.

### What Was Checked

- py_compile, 11-test suite, rg 매칭, git diff --check 재실행
- `app/handlers/preferences.py:186–221` 코드 직접 확인 (매핑 로직, task log, 반환값)
- `app/web.py:396,405-406` 코드 직접 확인 (라우트 등록)

### What Was Not Checked

- 전체 unittest discover 미실행: `test_preference_handler` 11개가 해당 변경 파일의 전체 커버이며 /work에서 이 범위만 검증했음. `web_app.py` 오기재 등 handoff 파일 불일치를 감안한 의도적 범위 유지.
- browser/e2e 미실행: Axis 1은 backend-only, UI 노출 없음. Axis 2에서 UI 추가 후 Playwright 적용 예정.

### Residual Risk

- UI 노출 없음: 현재 sync는 API 직접 호출로만 트리거 가능. M29 Axis 2에서 PreferencePanel에 sync count + 버튼 추가 예정.
- SQLite preference store의 fingerprint 중복 조회: `list_all()` fallback 경로로 처리하고 있으나 대규모 preference 환경에서는 성능 주의 필요 (현재 local-first, 소규모).
