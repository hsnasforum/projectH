# 2026-04-02 sqlite root-doc truth sync

**범위**: 루트 문서에서 SQLite를 "not implemented"로 적은 표현을 현재 구현 truth에 맞게 수정
**근거**: `verify/4/2/2026-04-02-sqlite-session-payload-path-fix-verification.md`에서 문서/코드 불일치 보고

---

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md` — "Not Implemented"에서 "SQLite persistence" 제거, "Partial / Opt-In" 섹션 추가
- `docs/ARCHITECTURE.md` — "Not Implemented"에서 "SQLite migration" 제거, "Partial / Opt-In" 섹션 추가
- `docs/TASK_BACKLOG.md` — "Not Implemented"에서 "SQLite persistence" 제거, "Partial / Opt-In" 섹션 추가
- `docs/NEXT_STEPS.md` — "Explicitly Deferred"의 "SQLite migration"을 "SQLite default rollout and corrections migration"으로 교체, opt-in seam 존재를 명시

---

## 사용 skill

- 없음

---

## 변경 이유

현재 코드에는 `storage/sqlite_store.py`(sessions, artifacts, preferences, task_log 4개 테이블), `storage/migrate.py`(JSON→SQLite CLI), `config/settings.py`의 `storage_backend='sqlite'` opt-in 설정이 실제로 존재하고 동작한다. 그러나 루트 문서 4개는 SQLite를 통째로 "not implemented" 또는 "deferred"로 적고 있어 operator truth가 어긋났다.

---

## 핵심 변경

4개 문서에서 "SQLite persistence" / "SQLite migration"을 "Not Implemented" / "Deferred" 목록에서 제거하고, 현재 truth만 반영하는 "Partial / Opt-In" 표현으로 교체:
- opt-in SQLite backend seam이 session/artifact/preference/task-log 경로에 존재
- JSON backend가 default로 유지
- corrections store는 여전히 JSON 기반
- full migration / default rollout은 아직 미완료

"SQLite fully shipped"라고 쓰지 않았으며, 전략/로드맵은 옮기지 않았다.

---

## 검증

문서-only slice이므로 자동 검증 대상 없음.
문서 수정 기준이 된 구현 truth:
- `storage/sqlite_store.py` — `SQLiteSessionStore`, `SQLiteTaskLogger`, `SQLiteArtifactStore`, `SQLitePreferenceStore` 존재
- `storage/migrate.py` — JSON→SQLite 마이그레이션 CLI 존재
- `config/settings.py:25` — `storage_backend: str = "json"` (default JSON)
- `app/web.py:44-56` — `storage_backend='sqlite'` 분기에서 SQLite store 연결
- `storage/correction_store.py` — JSON 기반만 존재 (SQLite 미이전)

---

## 남은 리스크

1. **corrections store SQLite 이전 미완**: 이번 slice 범위 밖.
2. **SQLite default 전환 미완**: 이번 slice 범위 밖.
3. **React frontend 미연결, 기타 루트 문서 stale**: 이번 slice 범위 밖.
