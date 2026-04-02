# 2026-04-02 sqlite session payload path-assumption fix

**범위**: `storage_backend='sqlite'`에서 `get_session_payload()` crash 복구
**근거**: `verify/4/2/2026-04-02-aggregate-reverse-notice-contract-recovery-verification.md`에서 `SQLiteTaskLogger.path` AttributeError 보고

---

## 변경 파일

- `storage/task_log.py` — `TaskLogger.iter_session_records()` 메서드 추가
- `storage/sqlite_store.py` — `SQLiteTaskLogger.iter_session_records()` 메서드 추가
- `app/serializers.py` — `_iter_task_log_records()`가 `self.task_logger.path` 직접 접근 대신 `iter_session_records()` 사용
- `tests/test_web_app.py` — `test_get_session_payload_works_with_sqlite_backend` 추가

---

## 사용 skill

- 없음

---

## 변경 이유

`app/serializers.py`의 `_iter_task_log_records()`가 `self.task_logger.path`를 직접 접근하여 JSONL 파일을 읽었다. JSON 기반 `TaskLogger`는 `.path` 속성이 있지만, SQLite 기반 `SQLiteTaskLogger`는 데이터를 SQLite 테이블에 저장하므로 `.path`가 없다. `storage_backend='sqlite'`로 `WebAppService`를 생성하면 `get_session_payload()` 호출 시 `AttributeError: 'SQLiteTaskLogger' object has no attribute 'path'`로 즉시 crash했다.

---

## 핵심 변경

양쪽 TaskLogger에 `iter_session_records(session_id)` 메서드 추가:
- `TaskLogger`: 기존 JSONL 파일 파싱 로직을 메서드로 캡슐화
- `SQLiteTaskLogger`: `task_log` 테이블에서 `session_id`로 조회

`_iter_task_log_records()`는 `self.task_logger.path` 직접 접근 20줄을 1줄 위임(`self.task_logger.iter_session_records(...)`)으로 교체.

---

## 검증

- `python3 -m py_compile` — 변경 3개 파일 컴파일 성공
- `python3 -m unittest -v tests.test_web_app` — **187 tests OK** (기존 186 + 새 SQLite 테스트 1)
- spot-check: `AppSettings(storage_backend='sqlite', ...)` → `WebAppService(...).get_session_payload('sqlite-session')` — crash 없이 정상 응답

---

## 남은 리스크

1. **SQLite corrections 마이그레이션 미구현**: corrections store는 여전히 JSON 기반. 이번 slice 범위 밖.
2. **SQLite를 default로 전환하지 않음**: 이번 slice는 crash 수정만. default 전환은 별도 결정 필요.
3. **React frontend 미연결, 루트 문서 미동기화**: 이번 slice 범위 밖.
