# 2026-04-23 M14 Axis 2 quality integration

## 변경 파일
- `core/delta_analysis.py`
- `scripts/export_traces.py`
- `storage/preference_store.py`
- `app/handlers/preferences.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_store.py`
- `tests/test_preference_handler.py`
- `docs/MILESTONES.md`
- `work/4/23/2026-04-23-m14-axis2-quality-integration.md`

## 사용 skill
- `doc-sync`: M13 Axis 5b 누락 기록과 M14 Axis 2 shipped 항목을 현재 구현에 맞춰 `docs/MILESTONES.md`에만 반영했습니다.
- `finalize-lite`: 구현 종료 전 실제 실행한 Python/unit/TypeScript/diff 검증과 남은 미검증 범위를 점검했습니다.
- `work-log-closeout`: closeout 형식과 실제 실행 결과를 맞춰 기록했습니다.

## 변경 이유
- handoff는 advisory seq 26 기준 M14 Axis 2 quality integration을 요청했습니다.
- M13 Axis 5b PreferencePanel reliability frontend는 이미 shipped였지만 `docs/MILESTONES.md` 기록이 Axis 5 frontend deferred 상태로 남아 있었습니다.
- `_is_high_quality()` threshold가 `scripts/export_traces.py`에만 있어 storage/API/frontend 표시 경로가 같은 품질 기준을 재사용할 수 없었습니다.

## 핵심 변경
- `core/delta_analysis.py`에 공개 helper `is_high_quality()`를 추가하고, `scripts/export_traces.py`는 기존 `_is_high_quality` 이름을 해당 helper re-export로 유지했습니다.
- JSON-backed `PreferenceStore.promote_from_corrections()`와 `_refresh_evidence()`가 correction `similarity_score` 평균을 `avg_similarity_score`로 저장하도록 했습니다.
- `list_preferences_payload()`가 각 preference에 `quality_info.avg_similarity_score`와 `quality_info.is_high_quality`를 추가하도록 했습니다.
- frontend `PreferenceRecord` 타입에 `quality_info`를 추가하고, `PreferencePanel.tsx`가 high-quality preference description 옆에 `고품질` badge를 표시하도록 했습니다.
- 평균 점수 저장과 handler enrichment 단위 테스트를 추가했고, M13 Axis 5b 및 M14 Axis 2 milestone 기록을 갱신했습니다.

## 검증
- `python3 -m py_compile core/delta_analysis.py scripts/export_traces.py storage/preference_store.py app/handlers/preferences.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_store tests.test_export_utility tests.test_preference_handler -v`
  - 통과: `38 tests`
- `git diff --check -- core/delta_analysis.py scripts/export_traces.py storage/preference_store.py app/handlers/preferences.py docs/MILESTONES.md`
  - 통과: 출력 없음
- `git diff --check -- core/delta_analysis.py scripts/export_traces.py storage/preference_store.py app/handlers/preferences.py docs/MILESTONES.md app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_store.py tests/test_preference_handler.py`
  - 통과: 출력 없음
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음

## 남은 리스크
- 전체 test suite와 Playwright browser smoke는 실행하지 않았습니다.
- badge UI는 TypeScript compile로만 확인했고, 실제 브라우저 스크린샷 검증은 이번 handoff acceptance 범위에 없어서 실행하지 않았습니다.
- SQLite preference quality parity는 handoff boundary에 따라 제외했습니다. `SQLitePreferenceStore.record_reviewed_candidate_preference()` 경로는 correction-level `similarity_score`를 갖지 않습니다.
