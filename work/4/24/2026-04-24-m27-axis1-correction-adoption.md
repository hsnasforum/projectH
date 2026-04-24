# 2026-04-24 M27 Axis 1 correction adoption tracking

## 변경 파일
- `storage/correction_store.py`
- `storage/sqlite_store.py`
- `scripts/audit_traces.py`
- `tests/test_correction_store.py`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m27-axis1-correction-adoption.md`

## 사용 skill
- `finalize-lite`: 구현 말미에 실제 변경 파일, 실행한 검증, 문서 동기화 필요 여부, closeout 준비 상태를 함께 점검했습니다.
- `work-log-closeout`: 이번 구현 라운드의 파일, 검증, 남은 리스크를 한국어 `/work` closeout으로 정리했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` `CONTROL_SEQ: 107`가 Milestone 27 Axis 1 `m27_axis1_correction_adoption_tracking`을 지시했습니다.
- 근거는 council convergence `seq 106/107`의 Option A 결정과 `verify/4/24/2026-04-24-m26-axes1-2-e2e-isolation.md` `CONTROL_SEQ 106`입니다.
- 기존 감사 출력은 incomplete correction 수는 보여주지만, fully adopted 상태인 `ACTIVE` correction 수를 볼 수 없어 adoption telemetry에 관찰 공백이 있었습니다.

## 핵심 변경
- JSON `CorrectionStore`에 `find_adopted_corrections()`를 추가해 `status == CorrectionStatus.ACTIVE` correction을 모으고 `activated_at` 기준으로 정렬하게 했습니다.
- `SQLiteCorrectionStore`에도 같은 public method를 추가했습니다. SQLite 쿼리는 `status = active`로 좁히고, JSON `data` blob에서 deserialization된 `activated_at` 기준으로 최종 정렬하게 맞췄습니다.
- `scripts/audit_traces.py`가 `find_adopted_corrections()`를 호출해 `Adopted corrections (ACTIVE): N` 한 줄을 추가 출력합니다.
- `tests/test_correction_store.py`에 JSON/SQLite 양쪽의 active-only 반환과 `activated_at` 오름차순 정렬 검증을 추가했습니다.
- `docs/MILESTONES.md`에 Milestone 27 정의, guardrails, Axis 1 shipped entry를 추가했습니다.

## 검증
- `python3 -m py_compile storage/correction_store.py storage/sqlite_store.py scripts/audit_traces.py tests/test_correction_store.py`
  - 통과: 출력 없음
- `python3 -m unittest -v tests/test_correction_store.py 2>&1 | tail -10`
  - 통과: `Ran 25 tests ... OK`
- `python3 scripts/audit_traces.py`
  - 통과: 감사 출력에 `Adopted corrections (ACTIVE): 0` 확인
- `git diff --check -- storage/correction_store.py storage/sqlite_store.py scripts/audit_traces.py docs/MILESTONES.md tests/test_correction_store.py`
  - 통과: 출력 없음

## 남은 리스크
- `python3 scripts/audit_traces.py`는 현재 로컬 JSON correction 데이터에서 `ACTIVE` correction이 0건인 상태를 확인했습니다. 양수 케이스는 새 store-level 단위 테스트에서 JSON/SQLite 모두 검증했습니다.
- `docs/MILESTONES.md`에는 이번 작업 전부터 runtime launcher 관련 미커밋 변경이 있었습니다. 이번 라운드는 그 기존 내용을 보존하고 M27 섹션만 추가했습니다.
- full unit discover와 browser/e2e suite는 handoff 범위를 넘어서 실행하지 않았습니다.
