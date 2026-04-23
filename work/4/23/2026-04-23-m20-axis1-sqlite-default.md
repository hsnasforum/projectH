# 2026-04-23 M20 Axis 1 sqlite default

## 변경 파일
- `config/settings.py`
- `app/web.py`
- `storage/sqlite_store.py`
- `tests/test_sqlite_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m20-axis1-sqlite-default.md`

## 사용 skill
- `security-gate`: 기본 저장소 전환과 startup migration이 로컬 SQLite/JSON 파일 경계 안에서만 동작하고, 실패 시 서버 시작을 막지 않는지 확인했습니다.
- `doc-sync`: M20 Axis 1 shipped behavior와 JSON override guardrail을 `docs/MILESTONES.md`에만 좁게 반영했습니다.
- `finalize-lite`: handoff acceptance check만 실행하고, 실제 대량 migration과 timing 검증은 통과로 적지 않았습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- advisory seq 77 / implement handoff seq 78 기준 SQLite를 기본 저장소 경로로 전환하고, 첫 SQLite startup에서 기존 correction JSON을 안전하게 옮길 수 있게 하기 위해서입니다.
- 기존 JSON backend는 `LOCAL_AI_STORAGE_BACKEND=json` 환경 변수 override로 유지해야 했습니다.

## 핵심 변경
- `config/settings.py`의 `storage_backend` 기본값과 `from_env()` fallback을 `"sqlite"`로 변경했습니다.
- `app/web.py`의 SQLite branch가 startup 때 `corrections` table row count를 확인하고, table이 비어 있으며 `settings.corrections_dir`에 JSON 파일이 있으면 correction migration만 조건부 실행합니다.
- startup migration은 mandatory `try/except`로 감싸 실패해도 서버 시작을 막지 않게 했습니다.
- `migrate_json_to_sqlite()`가 optional directory에 `None`을 받으면 해당 table family를 skip하도록 조정해 startup migration이 sessions/artifacts/preferences를 훑지 않게 했습니다.
- correction migration count를 `INSERT OR IGNORE`의 실제 inserted row count 기준으로 바꿔 idempotency를 검증할 수 있게 했습니다.
- `tests/test_sqlite_store.py`에 synthetic correction JSON을 임시 디렉터리에서 두 번 migrate해 두 번째 실행이 `corrections == 0`을 반환하는 regression test를 추가했습니다.
- `docs/MILESTONES.md`에 M20 Axis 1 SQLite default와 migration guardrail을 추가했습니다.

## 검증
- `python3 -m py_compile config/settings.py app/web.py storage/sqlite_store.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_sqlite_store -v`
  - 통과: `Ran 20 tests in 0.068s`, `OK`
  - handoff 예상은 기존 + 1개로 19개였지만, 현재 suite에는 이전 Axis 3의 `test_sqlite_update_description_changes_field`가 이미 포함되어 20개가 실행됐습니다.
- `git diff --check -- config/settings.py app/web.py docs/MILESTONES.md tests/test_sqlite_store.py`
  - 통과: 출력 없음
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- handoff boundary에 따라 실제 `data/corrections/` 8,000+ 파일 migration은 실행하지 않았습니다. 이번 검증은 synthetic temp data 기반 idempotency 확인입니다.
- 대량 migration 성능 timing은 handoff boundary에 따라 단위 테스트로 추가하지 않았고 실행하지 않았습니다. 첫 SQLite default startup은 correction JSON이 많으면 일회성 지연이 있을 수 있습니다.
- startup migration failure는 서버 시작을 막지 않도록 `except Exception: pass`로 처리됩니다. 실패 원인 관측/로그가 필요하면 별도 운영성 slice가 필요합니다.
- 기존 미추적 파일 `report/gemini/2026-04-23-m20-definition.md`는 이번 implement round에서 건드리지 않았습니다.
