# 2026-04-23 M13 Axis 6 auto activation

## 변경 파일
- `storage/preference_store.py`
- `tests/test_preference_store.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m13-axis6-auto-activation.md`

## 사용 skill
- `finalize-lite`: 구현 종료 시점의 범위 내 검증, 문서 반영, closeout 준비 여부를 함께 점검했습니다.
- `work-log-closeout`: `/work` 노트 형식과 필수 기록 항목을 맞춰 closeout를 작성했습니다.

## 변경 이유
- handoff 범위인 Milestone 13 Axis 6에서 `cross_session_count >= 3`인 반복 교정 선호를 자동 활성화해 candidate 단계에서 active 단계로 좁게 연결할 필요가 있었습니다.
- 기존 저장 구조와 테스트 패턴을 유지하면서 후보 상태에만 임계값 규칙을 추가해야 했습니다.

## 핵심 변경
- `storage/preference_store.py`에 `AUTO_ACTIVATE_CROSS_SESSION_THRESHOLD = 3` 상수를 추가하고, `CANDIDATE` 상태에서만 자동 승격하는 `_auto_activate_candidate_if_ready()` 헬퍼를 추가했습니다.
- 신규 선호 생성(`promote_from_corrections`)과 기존 선호 evidence refresh 경로 모두에서 단일 `atomic_write()` 전에 상태, `activated_at`, `updated_at`를 함께 정리하도록 연결했습니다.
- 자동 승격은 `cross_session_count >= 3`일 때만 적용되며, `ACTIVE`, `REJECTED`, `PAUSED` 상태 레코드는 threshold check 중 상태를 바꾸지 않도록 가드했습니다.
- `tests/test_preference_store.py`에 2세션 유지, 3세션 승격, 이미 `ACTIVE`인 레코드 유지, `REJECTED` 레코드 유지 케이스를 추가했고, refresh 시 3세션 도달 케이스가 `ACTIVE`로 바뀌는지도 검증했습니다.
- `docs/MILESTONES.md`에서 M13 Axis 6을 shipped로 표시하고 `cross_session_count >= 3` 규칙과 상태 가드를 현재 기준으로 반영했습니다.

## 검증
- `pytest tests/test_preference_store.py`
  - 통과: `20 passed`
- `python3 -m py_compile storage/preference_store.py`
  - 통과: 출력 없음
- `git diff --check -- storage/preference_store.py tests/test_preference_store.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 handoff 범위는 JSON 기반 `storage/preference_store.py`에 한정되어 있어 `storage/sqlite_store.py`의 `SQLitePreferenceStore`에는 같은 자동 활성화 규칙이 아직 반영되지 않았습니다.
- `docs/MILESTONES.md`는 이번 shipped 상태로 갱신했지만, 다른 상위 문서 중 일부는 activation 미구현 표현이 남아 있을 수 있어 후속 doc-sync가 필요합니다.
