# 2026-04-25 M37 sqlite migration completion

## 변경 파일
- `app/web.py`
- `docs/TASK_BACKLOG.md`
- `work/4/25/2026-04-25-m37-sqlite-migration-completion.md`

## 사용 skill
- `security-gate`: SQLite 첫 시작 마이그레이션이 session/artifact/preference/correction 저장 데이터를 다루는 local persistence 경로라서 저장 경계와 되돌림 리스크를 확인했습니다.
- `doc-sync`: SQLite 기본값 및 JSON→SQLite 마이그레이션 상태가 backlog 문구와 어긋나 있어 구현 사실에 맞게 정리했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 기록했습니다.

## 변경 이유
- `CONTROL_SEQ: 204` handoff에 따라 SQLite backend 첫 시작 migration이 corrections 외에 sessions, artifacts, preferences JSON dirs도 함께 전달하도록 완성해야 했습니다.
- `docs/TASK_BACKLOG.md`의 SQLite 설명이 `JSON backend remains default`, `Full migration and default rollout are deferred` 상태로 남아 있어 현재 SQLite 기본값과 M37 migration 경로를 반영해야 했습니다.

## 핵심 변경
- `app/web.py`의 `migrate_json_to_sqlite` 호출에서 `sessions_dir`, `artifacts_dir`, `preferences_dir`에 실제 settings path를 전달하도록 변경했습니다.
- 기존 `try/except Exception: pass` wrapper와 `corrections_path` 기반 migration 진입 조건은 유지했습니다.
- `storage/sqlite_store.py`, `config/settings.py`, frontend, watcher 파일은 수정하지 않았습니다.
- `docs/TASK_BACKLOG.md`에서 SQLite backend가 기본값임을 `config/settings.py DEFAULT_STORAGE_BACKEND = "sqlite"`와 함께 명시했습니다.
- backlog에 sessions, artifacts, preferences, corrections 전체 migration이 기존 JSON data가 있는 첫 시작에서 실행된다고 갱신했습니다.

## 검증
- `python3 -m py_compile app/web.py`
  - 통과, 출력 없음.
- `python3 -m unittest tests/test_sqlite_store.py -v 2>&1 | tail -5`
  - 통과.
  - `Ran 30 tests in 0.087s`
  - `OK`
- `git diff --check -- app/web.py docs/TASK_BACKLOG.md`
  - 통과, 출력 없음.

## 남은 리스크
- 전체 E2E gate는 실행하지 않았습니다. handoff가 E2E gate를 금지하고 targeted compile/unit/diff check만 지정했기 때문입니다.
- migration 진입 조건 자체는 기존처럼 corrections table과 corrections JSON presence를 기준으로 합니다. 이번 handoff 범위는 추가 dirs 전달과 backlog truth-sync에 한정했습니다.
- 작업 전부터 있던 `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md` 변경은 이번 implement handoff 범위 밖이라 건드리지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
