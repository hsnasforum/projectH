# 2026-04-28 M58 Axis 1 ArtifactRecord TypedDict

## 변경 파일

- `core/contracts.py`
- `storage/artifact_store.py`
- `tests/test_artifact_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m58-axis1-artifact-record-typeddict.md`

## 사용 skill

- `security-gate`: artifact store의 로컬 저장 record 표면을 만졌으므로 approval, overwrite/delete, 외부 네트워크, logging 경계가 바뀌지 않았는지 확인했습니다.
- `doc-sync`: handoff가 지정한 `docs/MILESTONES.md` M58 Axis 1 항목만 현재 구현 상태에 맞춰 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M54-M57에서 correction, preference, per-preference stats 타입 표면을 정리한 뒤, JSON 기반 `ArtifactStore`의 artifact record 반환 타입도 공식 계약으로 묶을 필요가 있었습니다. 이번 slice는 `ArtifactRecord`를 추가하고 `ArtifactStore`의 생성/조회/갱신/list 반환 annotation을 통일했습니다.

## 핵심 변경

- `core/contracts.py`에 `ArtifactRecord(TypedDict, total=False)`를 추가했습니다.
- `ArtifactRecord.latest_outcome`은 현재 `artifact_store.py`가 문자열 outcome을 저장하는 구현 truth를 반영해 `dict[str, Any] | str | None`으로 표기했습니다.
- `storage/artifact_store.py`에서 `ArtifactRecord`를 import하고 `create()`, `get()`, `append_correction()`, `append_save()`, `record_outcome()`, `list_by_session()`, `list_recent()` 반환 타입을 통일했습니다.
- `tests/test_artifact_store.py`에 `create()`가 typed artifact 핵심 필드와 빈 lifecycle list를 반환하는지 확인하는 테스트를 추가했습니다.
- `docs/MILESTONES.md`에 M58 Artifact Type Schema Axis 1 항목을 추가했습니다.

## 검증

- `python3 -m py_compile core/contracts.py storage/artifact_store.py tests/test_artifact_store.py`
  - 통과
- `python3 -m unittest -v tests.test_artifact_store`
  - 통과, 13개 테스트 OK
- `git diff --check -- core/contracts.py storage/artifact_store.py tests/test_artifact_store.py docs/MILESTONES.md`
  - 통과
- `rg -n -- "-> dict\\[str, Any\\]|-> list\\[dict\\[str, Any\\]\\]|ArtifactRecord" storage/artifact_store.py core/contracts.py tests/test_artifact_store.py docs/MILESTONES.md`
  - `storage/artifact_store.py`의 `dict[str, Any]` 반환 annotation 잔존 없음

## 남은 리스크

- `storage/sqlite_store.py`의 `SQLiteArtifactStore` 타입 표면은 handoff 경계상 Axis 2 대상이라 변경하지 않았습니다.
- 이번 변경은 type annotation, TypedDict, 단위 테스트, 마일스톤 기록에 한정했습니다. approval, session/preference store, frontend, dist, E2E는 변경하지 않았습니다.
- browser/E2E, 전체 unittest, 별도 정적 타입 검사 도구는 실행하지 않았습니다.
