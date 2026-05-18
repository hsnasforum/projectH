# 2026-04-29 M85 Axis 1 correction reliability seed

## 변경 파일
- `storage/preference_utils.py`
- `storage/preference_store.py`
- `storage/sqlite/preference.py`
- `app/handlers/corrections.py`
- `tests/test_correction_summary.py`
- `tests/test_preference_store.py`
- `work/4/29/2026-04-29-m85-axis1-correction-reliability-seed.md`

## 사용 skill
- `security-gate`: preference 저장 record의 `reliability_stats` 초기값 변경이 local-first 저장 경계를 벗어나지 않는지 확인했다.
- `finalize-lite`: 구현 후 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, closeout 준비 상태를 점검했다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 closeout note를 작성했다.

## 변경 이유
- explicit pattern promotion으로 생성된 preference가 기존에는 `reliability_stats.applied_count = 0`으로 시작해, correction의 반복 관찰 횟수가 있어도 `is_highly_reliable_preference`의 `applied_count >= 3` 조건을 즉시 만족할 수 없었다.
- correction의 `recurrence_count`를 신규 preference의 초기 reliability seed로 저장해, 승격 직후에도 반복 관찰 근거가 reliability 판정에 반영되도록 했다.

## 핵심 변경
- `seed_reliability_from_recurrence(recurrence_count)` 헬퍼를 추가해 1 이상 recurrence를 `{"applied_count": recurrence_count, "corrected_count": 0}`으로 변환한다.
- JSON `PreferenceStore.record_reviewed_candidate_preference`에 `initial_reliability_stats` 선택 파라미터를 추가하고, 신규 record 생성 시에만 `reliability_stats` 초기값으로 저장한다.
- SQLite `SQLitePreferenceStore.record_reviewed_candidate_preference`에도 동일 파라미터와 신규 record seed 저장을 추가했다.
- `CorrectionHandlerMixin.promote_correction_pattern`에서 promoted correction의 `recurrence_count`를 preference 생성 호출에 전달한다.
- 승격 시 seed 저장과 idempotent 갱신 경로의 기존 `reliability_stats` 보존을 단위 테스트로 고정했다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: 요청된 `67e22a1d002b697880af4fc8f16a29a229fc1a21ccb109ca90d73ada483e2a5a`와 일치.
- `git switch -c feat/m85-axis1-correction-reliability-seed` 실행: `.git/refs/heads/...lock` 생성이 read-only filesystem으로 막혀 실패. 브랜치 생성은 환경 제약으로 완료하지 못했다.
- `python3 -m py_compile storage/preference_utils.py storage/preference_store.py storage/sqlite/preference.py app/handlers/corrections.py tests/test_preference_store.py tests/test_correction_summary.py` 통과.
- `python3 -m py_compile storage/preference_utils.py storage/preference_store.py app/handlers/corrections.py storage/sqlite/preference.py` 통과.
- `python3 -m unittest -v tests.test_correction_summary tests.test_preference_store` 통과 (`Ran 39 tests ... OK`).
- `python3 -m unittest -v tests.test_preference_handler` 통과 (`Ran 20 tests ... OK`).
- `python3 -m unittest -v tests.test_sqlite_store` 통과 (`Ran 43 tests ... OK`).
- `python3 -m unittest -v tests.test_watcher_core` 통과 (`Ran 208 tests ... OK`).
- `git diff --check -- storage/preference_utils.py storage/preference_store.py storage/sqlite/preference.py app/handlers/corrections.py tests/test_preference_store.py tests/test_correction_summary.py` 통과.

## 남은 리스크
- 브랜치 생성은 `.git/refs` 쓰기 제한 때문에 실패했으므로 변경은 현재 `feat/m84-doc-sync-m81-m83` 작업트리에 남아 있다.
- handoff가 신규 단위 테스트 2건을 요구했기 때문에 `tests/test_correction_summary.py`와 `tests/test_preference_store.py`를 수정했다. dist, E2E, frontend 파일은 수정하지 않았다.
- 이번 라운드는 Axis 1만 구현했다. PreferencePanel UI reliability 표시, 문서 milestone 갱신, commit/push/PR publish, `/verify` 작성은 수행하지 않았다.
