# 2026-04-20 sqlite summary hint G6-sub1 verification

## 변경 파일
- `verify/4/20/2026-04-20-sqlite-summary-hint-g6-sub1-verification.md`

## 사용 skill
- `round-handoff`: seq 459 `.pipeline/claude_handoff.md`(G6-sub1, Gemini 458 advice) 구현 주장을 `storage/sqlite_store.py`, `tests/test_web_app.py` 실제 상태와 대조했고, handoff가 요구한 narrowest 재검증(두 대상 test 직접 재실행, `tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`, `py_compile`, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 459 `.pipeline/claude_handoff.md`(Gemini 458 advice 기반 G6-sub1)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-sqlite-summary-hint-g6-sub1.md`가 제출되었습니다.
- 목표는 `SQLiteSessionStore`의 adoption list에 `_compact_summary_hint_for_persist` 하나를 추가해 27개 SQLite-backed `AttributeError` 클러스터를 닫고, 동시에 `tests/test_web_app.py:14994`의 stale wording 1줄을 seq 441 focus-slot WEAK single-source wording에 맞춰 truth-sync하는 것이었습니다.

## 핵심 변경
- `storage/sqlite_store.py:343` 신규 adoption line
  - 실제 구현은 `_compact_summary_hint_for_persist = staticmethod(_SS._compact_summary_hint_for_persist)`로, handoff의 literal `= _SS._compact_summary_hint_for_persist`에서 한 걸음 refinement. 이유: `SessionStore._compact_summary_hint_for_persist`는 `@staticmethod` 데코레이터로 선언되어 있어서(`storage/session_store.py:789`), 클래스 속성 접근 시 Python descriptor 프로토콜이 내부 함수를 unwrap합니다. plain assignment만 하면 class attribute가 일반 함수가 되고 `self._compact_summary_hint_for_persist(text, ...)` 호출 시 `self`가 `text` 자리로 바인딩돼 call이 잘못됩니다. `staticmethod(...)`로 다시 감싸면 descriptor가 보존돼 `self` 바인딩 없이 올바른 호출이 가능합니다. 이 deviation은 implementer가 "plain adoption → TypeError → staticmethod parity → green" 경로로 발견했고 `/work`가 솔직하게 기록했습니다. verify/handoff owner의 handoff 지시에서 놓친 Python 세부사항의 올바른 correction입니다.
  - 배치는 `:342` `_current_correctable_text = _SS._current_correctable_text` 바로 다음, `:344` `# Public session-data methods` divider 바로 앞. handoff 위치 지시와 일치.
  - 들여쓰기는 class body 4칸으로 주변 adoption line과 정합.
- `storage/sqlite_store.py:318-354` 나머지 adoption list 미변경 확인. `from storage.session_store import SessionStore as _SS` import(`:323`), `del _SS` cleanup(`:354`), 다른 20+ 어답션 모두 그대로.
- `tests/test_web_app.py:14994` wording truth-sync
  - `self.assertIn("한 가지 출처의 정보로만 확인됩니다", summary)`. 주변 `:14990-14993`(`assertIsNotNone`, `assertIn "재조사했지만"`, `assertIn "이용 형태"`, `assertIn "아직"`)와 `:14995-14996`(`assertNotIn "보강"`, `assertNotIn "미확인에서"`) 모두 유지됨. handoff 지시와 정합.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456 shipped 표면은 전부 미편집 확인. `storage/session_store.py`, `core/*`, `app/*`, `tests/test_smoke.py`, client/serializer/Playwright, `status_label` literal set, legend 모두 그대로. `git diff --check` 출력 0건.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `459` — shipped 됐고 새 `/work`로 소비됨. 다음 라운드는 seq 460.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `457` — seq 458 advice로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `458` — seq 459 handoff로 변환되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `424` — shipping으로 자연 해제 유지. real operator-only blocker 없음.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_persists_local_preference_candidate_with_sqlite_backend`
  - 결과: `Ran 1 test in 0.132s`, `OK`. SQLite-backed adoption 경로가 정상 동작함을 직접 확인.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_handle_chat_load_web_search_record_id_legacy_claim_coverage_slots_surface_canonical_slots_and_truthful_progress`
  - 결과: `Ran 1 test in 0.018s`, `OK`. `:14994` truth-sync가 seq 441 wording과 정합함을 직접 확인.
- `python3 -m unittest tests.test_smoke -k progress_summary`
  - 결과: `Ran 11 tests in 0.014s`, `OK`. seq 453 baseline 유지.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 27 tests in 0.052s`, `OK`. seq 453 baseline 유지.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 7 tests in 0.001s`, `OK`. seq 427 baseline 유지.
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 6 tests in 0.059s`, `OK`. seq 423 baseline 유지.
- `python3 -m py_compile storage/sqlite_store.py tests/test_web_app.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- storage/sqlite_store.py tests/test_web_app.py`
  - 결과: 출력 없음, 통과.
- 전체 `tests.test_web_app` 162초짜리 재실행은 이번 verify 라운드에서는 `/work`가 이미 수행·기록한 결과(`failures=1, errors=27 → errors=10`, 모두 `LocalOnlyHTTPServer` bind `PermissionError`)를 신뢰하고 두 대상 메서드 단위 재실행으로 대체했습니다. `/work`의 residual 10건은 이 slice와 무관한 socket/환경 문제이므로 verify 범위 밖입니다.
- `node --check`, Playwright, `make e2e-test`, `tests.test_pipeline_gui_backend`는 이번 라운드가 storage + test wording slice라 의도적으로 생략.

## 남은 리스크
- **SQLiteSessionStore adoption list drift**: 여전히 수동 유지. 앞으로 `SessionStore`에 private helper가 추가될 때마다 같은 `AttributeError`가 재발할 여지가 있습니다. property-style parity check나 shared adoption 메커니즘을 도입하는 meta-slice를 후속 arbitration 후보로 남깁니다.
- **@staticmethod adoption 패턴 일관성**: 이번 slice는 `staticmethod(_SS._compact_summary_hint_for_persist)` 한 건만 다시 감쌌고, 주변 20+ 어답션은 plain `= _SS.xxx` 형태입니다. 그 중 실제 `@staticmethod`로 선언된 것(예: `_backfill_active_context_summary_hint_basis`는 SQLiteSessionStore 내부에서 `_SS._backfill_active_context_summary_hint_basis(data)`로 직접 호출되므로 adoption이 아예 필요 없음)이 어느 정도인지는 별도 감사가 필요합니다. 현재 shipped 동작은 `self.xxx()`로 호출하는 path가 있는 모든 staticmethod만 wrapping이 필요합니다. 이 감사는 위 meta-slice로 함께 다룰 수 있습니다.
- **tests/test_web_app.py legacy `"단일 출처 상태"` fixture/assert 잔존**: `rg`가 14건(`:15009`, `:15068`, `:15080`, `:15102`, `:15187`, `:15270`, `:15370`, `:15567`, `:15771`, `:17981`, `:18139`, `:18158`, `:18296`, `:18301`) 잡힙니다. 모두 legacy progress_summary fixture text거나 별도 path의 assert로 보이며, 현재 `tests.test_web_app` 실행 결과에서는 해당 테스트들이 wording 실패로 red가 아닌 상태입니다(`errors=10`은 전부 PermissionError). 이는 fixture 안 legacy string이 해당 테스트의 실제 검증 경로에서 다시 canonicalize되어 다른 wording으로 비교되기 때문으로 추정됩니다. 후속 slice에서 불필요한 legacy fixture string을 정리할지는 별도 판단이 필요합니다.
- **residual 10 PermissionError (LocalOnlyHTTPServer bind)**: `[Errno 1] Operation not permitted`로 socket bind가 막히는 환경/샌드박스 문제. 이번 slice와 무관한 별도 G6-sub2 axis로 분류할 수 있으나, 테스트가 TCP bind를 시도하는 구조라 재발 가능성이 높고 환경 제약 해제가 operator decision에 가까울 수 있습니다.
- **다음 슬라이스 ambiguity**: G3(threshold tuning), G5(`tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state), G6-sub2(LocalOnlyHTTPServer bind family), G6-sub3(legacy `"단일 출처 상태"` fixture cleanup 가치 판단), G7(vocabulary enforcement), G8(memory foundation), G9(naming-collision cleanup), G10(COMMUNITY explicit key), G11 NEW(`SQLiteSessionStore` adoption list meta-audit)가 모두 서로 다른 축. dominant current-risk reduction은 뚜렷하지 않고, G6-sub2의 socket bind는 operator 결정이 포함될 수 있어 Gemini arbitration으로 우선순위 + 경계 구분을 먼저 받는 편이 `/verify` README 규칙과 일치합니다(CONTROL_SEQ 460).
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. storage + test slice라 docs drift 없음. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드 비편집.
