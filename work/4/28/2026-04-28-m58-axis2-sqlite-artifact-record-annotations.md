# 2026-04-28 M58 Axis 2 SQLiteArtifactStore ArtifactRecord 반환 타입 정리

## 변경 파일
- `storage/sqlite_store.py`
- `tests/test_artifact_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m58-axis2-sqlite-artifact-record-annotations.md`

## 사용 skill
- `security-gate`: SQLite artifact 저장소의 로컬 레코드 반환 표면만 확인했습니다. 승인, 네트워크, 파일 overwrite, 외부 실행 경계는 변경하지 않았습니다.
- `doc-sync`: 현재 M58 Axis 2 진행 사실을 `docs/MILESTONES.md`에만 반영했습니다.
- `work-log-closeout`: 구현 변경, 실제 검증, 남은 리스크를 closeout으로 정리했습니다.

## 변경 이유
- M58 Axis 1에서 `ArtifactRecord` TypedDict와 JSON artifact store 반환 타입이 정리되었지만, SQLite artifact store 반환 타입 표면은 아직 일반 `dict` 계열 주석으로 남아 있었습니다.
- handoff의 M58 Axis 2 범위에 맞춰 `SQLiteArtifactStore`의 반환 타입 주석을 `ArtifactRecord` 중심으로 맞추고, SQLite 경로가 실제 dict 호환 typed record를 반환한다는 회귀 테스트를 추가했습니다.

## 핵심 변경
- `storage/sqlite_store.py`에서 `ArtifactRecord`를 import하고 `SQLiteArtifactStore.create`, `get`, `list_by_session`, `list_recent` 반환 타입을 `ArtifactRecord` 또는 `list[ArtifactRecord]`로 변경했습니다.
- SQLite artifact 저장 로직, 스키마, 쿼리, 승인/저장 플로우 동작은 변경하지 않았습니다.
- `tests/test_artifact_store.py`에 SQLite create 경로가 `ArtifactRecord`로 할당 가능하고 주요 필드를 보존한다는 테스트를 추가했습니다.
- `docs/MILESTONES.md`에 CONTROL_SEQ 1192의 M58 Axis 2 진행 항목을 추가했습니다.

## 검증
- 통과: `python3 -m py_compile storage/sqlite_store.py tests/test_artifact_store.py`
- 통과: `python3 -m unittest -v tests.test_artifact_store` (14 tests OK)
- 통과: `git diff --check -- storage/sqlite_store.py tests/test_artifact_store.py docs/MILESTONES.md`

## 남은 리스크
- 이번 변경은 타입 주석, 단위 테스트, milestone 문서에 한정되어 브라우저/E2E와 전체 unittest는 실행하지 않았습니다.
- 정적 타입 검사기는 실행하지 않았습니다.
- handoff 제외 범위인 `core/contracts.py`, `storage/artifact_store.py`, `SQLitePreferenceStore`, `SQLiteCorrectionStore`, `SQLiteDatabase`, approval/frontend/dist/E2E는 변경하지 않았습니다.
