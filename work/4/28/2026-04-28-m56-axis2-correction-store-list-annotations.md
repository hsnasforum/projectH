# 2026-04-28 M56 Axis 2 CorrectionStore list annotation

## 변경 파일

- `storage/correction_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m56-axis2-correction-store-list-annotations.md`

## 사용 skill

- `security-gate`: correction store의 로컬 저장 기록 표면을 만졌으므로 write path, approval, 외부 네트워크, logging 동작이 바뀌지 않았는지 확인했습니다.
- `doc-sync`: handoff가 지정한 `docs/MILESTONES.md` M56 Axis 2 항목만 현재 구현 상태에 맞춰 좁게 반영했습니다.
- `work-log-closeout`: 구현 종료 기록과 실제 검증 결과를 남겼습니다.

## 변경 이유

M54에서 `CorrectionRecord` TypedDict가 추가되고 `record_correction()`/`get()`/lifecycle 반환 타입이 정리됐지만, `CorrectionStore`의 list/query 계열 메서드는 아직 `list[dict[str, Any]]` 반환 annotation을 유지하고 있었습니다. 이번 slice는 해당 반환 타입을 `list[CorrectionRecord]`로 통일했습니다.

## 핵심 변경

- `storage/correction_store.py`의 `_scan_all()` 반환 annotation을 `list[CorrectionRecord]`로 변경했습니다.
- fingerprint, artifact, session, recent, incomplete, adopted correction list/query 메서드 반환 annotation을 `list[CorrectionRecord]`로 변경했습니다.
- `find_recurring_patterns()`와 내부 `groups` annotation도 handoff 범위에 맞춰 `CorrectionRecord` 표면으로 맞췄습니다.
- `docs/MILESTONES.md`에 M56 Axis 2 항목을 추가했습니다.
- 저장 로직, lifecycle transition, approval, frontend, SQLite store는 변경하지 않았습니다.

## 검증

- `python3 -m py_compile storage/correction_store.py`
  - 통과
- `python3 -m unittest -v tests.test_correction_store`
  - 통과, 27개 테스트 OK
- `git diff --check -- storage/correction_store.py docs/MILESTONES.md`
  - 통과
- `rg -n -- "-> list\\[dict\\[str, Any\\]\\]" storage/correction_store.py`
  - 매치 없음

## 남은 리스크

- 이번 변경은 annotation과 마일스톤 기록만 포함하므로 browser/E2E와 전체 unittest는 실행하지 않았습니다.
- 별도 정적 타입 검사 도구는 실행하지 않았습니다.
- `find_recurring_patterns()`는 런타임상 grouped pattern projection을 반환하지만, 이번 handoff 범위는 별도 projection TypedDict 추가가 아니라 기존 list 반환 annotation 통일이었습니다.
