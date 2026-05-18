# 2026-04-28 M68 Axis 1 promote-pattern

## 변경 파일
- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `app/handlers/aggregate.py`
- `app/web.py`
- `tests/test_correction_store.py`
- `tests/test_sqlite_store.py`

## 사용 skill
- `security-gate`: confirmed correction pattern을 PreferenceRecord로 승격하는 POST/write-capable 경로가 local-first, same-origin, 기존 저장소 전이/idempotency 경계를 유지하는지 점검했습니다.
- `work-log-closeout`: 이번 implement 라운드의 실제 변경 파일, 검증, 잔여 리스크를 `/work` 형식으로 기록했습니다.

## 변경 이유
- M68 Axis 1 핸드오프에 따라 운영자가 `CONFIRMED`로 승인한 correction pattern을 `PROMOTED` 상태로 전환하고, 기존 `record_reviewed_candidate_preference` 계약을 통해 PreferenceRecord 후보로 승격하는 backend 경로가 필요했습니다.

## 핵심 변경
- `CorrectionStore.promote_by_fingerprint()`를 추가해 동일 fingerprint의 correction 중 `CorrectionStatus.CONFIRMED` 상태만 `PROMOTED`로 전환하도록 했습니다.
- `SQLiteCorrectionStore.promote_by_fingerprint()`에 JSON store와 같은 상태 필터 및 전이 동작을 추가했습니다.
- `AggregateHandlerMixin.promote_correction_pattern()`을 추가해 `delta_fingerprint` payload를 검증하고, 승격된 correction마다 기존 preference store idempotency 계약으로 reviewed candidate preference를 기록하도록 했습니다.
- `POST /api/corrections/promote-pattern` 라우트를 허용 목록과 `do_POST` dispatch에 추가했습니다.
- JSON/SQLite store 단위 테스트에 confirmed-only promotion, `RECORDED`/`STOPPED` skip, missing fingerprint empty 반환 케이스를 추가했습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` → `1e26244da50dfaa7d18373483a391cb8d159685f6f190275606f7d342628f68e` 일치
- `git diff --name-status HEAD..origin/main -- storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py tests/test_correction_store.py tests/test_sqlite_store.py` → 차이 없음
- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py` → PASS
- `python3 -m unittest -v tests.test_correction_store` → PASS, 31 tests
- `python3 -m unittest -v tests.test_sqlite_store` → PASS, 35 tests
- `git diff --check -- storage/correction_store.py storage/sqlite_store.py app/handlers/aggregate.py app/web.py tests/test_correction_store.py tests/test_sqlite_store.py` → PASS

## 남은 리스크
- 핸드오프의 새 브랜치 생성 지시(`git switch -c feat/m68-axis1-promote-pattern origin/main`)는 샌드박스의 `.git/index.lock` 쓰기 제한으로 실패했습니다. 대상 파일은 현재 HEAD와 `origin/main` 사이 차이가 없음을 확인한 뒤 현재 작업트리에 같은 패치를 적용했습니다.
- Frontend 버튼 및 dist/E2E는 핸드오프상 M68 Axis 2 범위라 이번 라운드에서 수정하지 않았습니다.
- commit, push, PR 생성은 수행하지 않았습니다.
