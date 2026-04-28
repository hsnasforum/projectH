# 2026-04-28 M50 Axis 2 corrected_count 집계 범위 확장

## 변경 파일

- `storage/session_store.py`
- `tests/test_session_store.py`
- `docs/MILESTONES.md`
- `work/4/28/2026-04-28-m50-axis2-corrected-count-scope.md`

## 사용 skill

- `security-gate`: session record 정규화와 cross-session 집계 변경이 로컬 저장 record에 미치는 범위를 확인.
- `doc-sync`: 구현 사실을 `docs/MILESTONES.md`의 M50 항목에 제한적으로 반영.
- `work-log-closeout`: 구현 종료 기록을 표준 `/work` 형식으로 작성.

## 변경 이유

- `get_global_audit_summary()`가 `applied_preference_ids`가 있는 일반 chat 응답의 교정을 `corrected_count`에 반영하지 못했다.
- 기존 집계는 `artifact_kind == "grounded_brief"`일 때만 personalized correction으로 보아, applied preference가 들어간 chat 응답이 교정되어도 신뢰도 통계가 낮게 잡힐 수 있었다.

## 핵심 변경

- `get_global_audit_summary()`의 personalized correction 조건에서 `artifact_kind == "grounded_brief"` 제한을 제거하고 `corrected_text is not None`만 보도록 변경했다.
- `SessionStore._normalize_message()`에서 assistant 메시지에 `applied_preference_ids`가 있으면 non-grounded 응답의 `corrected_text`도 보존하도록 했다. 첫 테스트 실행에서 정규화 단계가 해당 필드를 제거하는 것을 확인해 같은 파일 안에서 최소 보정했다.
- `tests/test_session_store.py`에 `test_corrected_count_includes_non_grounded_brief_corrections`를 추가해 chat 응답 2건 중 교정된 1건만 `corrected_count`에 반영되는지 검증했다.
- `docs/MILESTONES.md` M50 섹션에 CONTROL_SEQ 1167 Axis 2 항목을 추가했다.
- security boundary: 변경은 로컬 session record 정규화와 read-side 집계에 한정된다. approval, overwrite/delete, web search, external action, preference lifecycle API는 변경하지 않았다.

## 검증

- `python3 -m py_compile storage/session_store.py tests/test_session_store.py`
  - 통과.
- `python3 -m unittest -v tests.test_session_store`
  - 1차 실패: 신규 테스트에서 `corrected_count`가 0으로 남음. 원인은 `_normalize_message()`가 non-grounded `corrected_text`를 제거했기 때문.
  - 정규화 보존 조건 추가 후 재실행 통과. `Ran 18 tests ... OK`.
- `git diff --check -- storage/session_store.py tests/test_session_store.py docs/MILESTONES.md`
  - 통과.

## 남은 리스크

- 범위가 session store 집계와 해당 단위 테스트에 제한되어 broad unit, Playwright, dist rebuild는 실행하지 않았다.
- `record_correction_for_message()`는 여전히 grounded-brief correction 제출 경로만 허용한다. 이번 변경은 이미 session record에 `applied_preference_ids + corrected_text`가 존재하는 applied-preference 응답을 정규화/집계에서 보존하는 범위다.
