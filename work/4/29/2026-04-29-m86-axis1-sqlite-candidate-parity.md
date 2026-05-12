# 2026-04-29 M86 Axis 1 SQLite 후보 선호 조회 parity

## 변경 파일
- `storage/sqlite/preference.py`
- `tests/test_sqlite_store.py`
- `work/4/29/2026-04-29-m86-axis1-sqlite-candidate-parity.md`

## 사용 skill
- `work-log-closeout`: 구현 라운드의 변경 파일, 실제 실행 검증, 남은 리스크를 한국어 closeout으로 정리했다.

## 변경 이유
- JSON `PreferenceStore`에는 `get_candidates()`와 `find_by_fingerprint()` 공개 메서드가 있지만 `SQLitePreferenceStore`에는 같은 조회 API가 없어 SQLite 백엔드에서 후보 선호 조회를 `list_all()` 전체 스캔에 의존해야 했다.
- cross-session memory foundation에서 SQLite 저장소도 JSON 저장소와 같은 후보 선호 조회 계약을 제공하도록 맞췄다.

## 핵심 변경
- `SQLitePreferenceStore`에 SQLite row를 `PreferenceRecord`로 복원하고 유효성 검사를 적용하는 `_record_from_row()` helper를 추가했다.
- `get_candidates(limit=50)`를 추가해 `status = 'candidate'` 레코드를 `updated_at DESC` 순서로 조회하게 했다.
- `find_by_fingerprint(delta_fingerprint)`를 추가해 fingerprint 일치 선호를 직접 조회하고, 없으면 `None`을 반환하게 했다.
- 기존 `list_all()`도 같은 row 복원 helper를 사용하도록 정리해 신규 조회 메서드와 레코드 구성 방식을 맞췄다.
- `tests/test_sqlite_store.py`에 candidate-only 조회와 fingerprint hit/miss 반환 단위 테스트를 추가했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: 요청된 `a57b5015b372ad366341cf3ce8a283ca0e3d08fcc1f6834de386135742c84aa0`와 일치.
- `git switch -c feat/m86-axis1-sqlite-candidate-parity` 실패: `.git/refs/...lock` 생성이 읽기 전용 파일 시스템으로 차단됨.
- `python3 -m py_compile storage/sqlite/preference.py tests/test_sqlite_store.py` 통과.
- `python3 -m unittest -v tests.test_sqlite_store` 통과: 45 tests OK.
- `python3 -m unittest -v tests.test_preference_store` 통과: 34 tests OK.
- `git diff --check -- storage/sqlite/preference.py tests/test_sqlite_store.py` 통과.
- `git diff --name-only -- app app/static/dist e2e` 출력 없음.
- `git status --short -- app app/static/dist e2e` 출력 없음.

## 남은 리스크
- 로컬 브랜치 생성은 `.git/refs` 쓰기 제한으로 수행하지 못했다. 커밋, push, branch/PR publish는 하지 않았고, 현재 checkout에서 허용된 소스/테스트 파일과 이 closeout만 변경했다.
- 변경 범위가 SQLite preference store 공개 조회 API와 단위 테스트에 한정되어 broad unittest와 browser/E2E는 실행하지 않았다.
