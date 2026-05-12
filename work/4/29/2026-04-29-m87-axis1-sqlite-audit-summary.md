# 2026-04-29 M87 Axis 1 SQLite 전역 감사 요약 parity

## 변경 파일
- `storage/sqlite/session.py`
- `tests/test_sqlite_store.py`
- `work/4/29/2026-04-29-m87-axis1-sqlite-audit-summary.md`

## 사용 skill
- `security-gate`: SQLite 세션 저장 레코드를 읽어 집계하는 경로가 로컬 read-only 경계 안에 남는지 확인했다.
- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 실행 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- JSON `SessionStore`에는 `get_global_audit_summary()`가 있어 전체 세션의 feedback, correction, applied preference 통계를 집계하지만 `SQLiteSessionStore`에는 같은 공개 메서드가 없었다.
- SQLite 백엔드에서는 `app/handlers/preferences.py`의 fallback 때문에 `per_preference_stats`가 빈 dict로 남아 live correction outcome 없이 초기 seed 중심으로 reliability가 계산될 수 있었다.

## 핵심 변경
- `SQLiteSessionStore.get_global_audit_summary()`를 추가해 SQLite `sessions.data` 전체를 읽고 JSON 세션 저장소와 같은 summary shape를 반환하게 했다.
- 메시지의 grounded-brief correction pair, feedback like/dislike, personalized response/correction count, `applied_preference_ids` 기반 per-preference applied/corrected count를 집계한다.
- `preference_correction_events[].fingerprint` 기반 corrected count도 `per_preference_stats`에 반영한다.
- 세션 단위 feedback과 `operator_action_history.status` (`executed`/`rolled_back`/`failed`) 집계도 JSON `SessionStore` 동작에 맞췄다.
- `tests/test_sqlite_store.py`에 empty summary와 per-preference stats 집계 테스트를 추가하고 SQLite session adoption list에 `get_global_audit_summary`를 포함했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: 요청된 `5bc3f18fd4e0eca4810eaf2c3414bae17d02ecab9c59ae46a5fc8b2598874c97`와 일치.
- `git branch --show-current && git rev-parse --short HEAD` 확인: `feat/m86-bundle`, `fc58007`.
- `git switch -c feat/m87-axis1-sqlite-audit-summary` 실패: `.git/refs/...lock` 생성이 읽기 전용 파일 시스템으로 차단됨.
- `python3 -m py_compile storage/sqlite/session.py tests/test_sqlite_store.py` 통과.
- `python3 -m unittest -v tests.test_sqlite_store` 통과: 47 tests OK.
- `python3 -m unittest -v tests.test_preference_handler` 통과: 20 tests OK.
- `git diff --check -- storage/sqlite/session.py tests/test_sqlite_store.py` 통과.
- `git status --short -- app app/static/dist e2e` 출력 없음.

## 남은 리스크
- 이번 변경은 저장된 SQLite session JSON을 읽어 집계만 수행한다. 세션 쓰기, approval/save 실행, overwrite/delete, 외부 web search, 로그 전송 동작은 추가하지 않았다.
- JSON `SessionStore`는 그대로 두었고, SQLite 쪽 구현은 현재 JSON 메서드의 실제 동작(`operator_action_history.status`, 세션 feedback 집계 포함)에 맞췄다.
- 로컬 브랜치 생성은 `.git/refs` 쓰기 제한으로 수행하지 못했다. commit, push, branch/PR publish는 하지 않았다.
- 변경 범위가 SQLite session store parity와 단위 테스트에 한정되어 broad unittest와 browser/E2E는 실행하지 않았다.
