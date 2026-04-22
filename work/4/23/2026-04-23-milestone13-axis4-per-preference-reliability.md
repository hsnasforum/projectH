# 2026-04-23 Milestone 13 Axis 4 per-preference reliability

## 변경 파일
- `storage/session_store.py`
- `scripts/audit_traces.py`
- `tests/test_session_store.py`
- `work/4/23/2026-04-23-milestone13-axis4-per-preference-reliability.md` (이 파일)

## 사용 skill
- `security-gate`: session summary와 audit 출력이 로컬 session 기록 기반 읽기/집계 범위에 머무르는지 확인했다.
- `finalize-lite`: 지정 검증 결과와 implement-lane 금지사항 준수 여부를 점검했다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 Korean closeout으로 남겼다.

## 변경 이유
- M13 Axis 3의 글로벌 personalized response/correction counter만으로는 특정 preference fingerprint별 correction 유발 여부를 볼 수 없었다.
- CONTROL_SEQ 969 handoff에 따라 per-preference reliability baseline을 추가해 향후 preference 활성화 판단의 근거를 남길 수 있게 했다.

## 핵심 변경
- `SessionStore.get_global_audit_summary()` summary dict에 `per_preference_stats`를 추가했다.
- `applied_preference_ids`가 있는 message마다 preference fingerprint별 `applied_count`를 누적하고, grounded brief + `corrected_text`가 있으면 `corrected_count`도 함께 누적한다.
- `scripts/audit_traces.py`가 per-preference correction rate를 correction rate 기준 내림차순으로 출력한다.
- personalized response가 없으면 `Per-preference reliability: N/A (no personalized responses yet)`를 출력한다.
- `tests/test_session_store.py`에 `pref-A`와 `pref-B`의 적용/교정 카운트를 검증하는 focused test를 추가했다.
- `preference_store.py`, `agent_loop.py`, `correction_store.py`, 계약 파일, `.pipeline` control slot은 수정하지 않았다.

## 검증
- `python3 -m py_compile storage/session_store.py scripts/audit_traces.py`
  - 통과, 출력 없음
- `python3 -m unittest tests.test_session_store tests.test_operator_executor tests.test_eval_loader tests.test_operator_audit tests.test_export_utility tests.test_promote_assets tests.test_evaluate_traces -v 2>&1 | tail -5`
  - `Ran 60 tests in 0.064s`
  - `OK`
- `python3 scripts/audit_traces.py`
  - `per_preference_stats`: `{}`
  - `Personalized responses:   0`
  - `Personalization correction rate: N/A (no personalized responses yet)`
  - `Per-preference reliability: N/A (no personalized responses yet)`
- `git diff --check -- storage/session_store.py scripts/audit_traces.py`
  - 통과, 출력 없음
- `git diff --check -- storage/session_store.py scripts/audit_traces.py tests/test_session_store.py`
  - 통과, 출력 없음

## 남은 리스크
- 현재 로컬 데이터 기준 active preferences와 personalized response가 0건이라 per-preference reliability는 아직 N/A다. 실제 reliability는 active preference 적용 이후 데이터가 쌓여야 의미가 생긴다.
- 이번 slice는 audit baseline만 추가했다. preference 활성화, 자동화 정책, UI 표시, 효과 판정 기준 변경은 포함하지 않았다.
- 기존 untracked `report/gemini/2026-04-23-m13-axis4-per-preference-audit.md`와 `work/4/23/2026-04-23-milestone13-axis3-commit-push.md`는 선행 작업물로 남아 있으며 이번 round에서 수정하지 않았다.
- 커밋, 푸시, PR 생성, next-slice 선택, `.pipeline` control slot 작성은 수행하지 않았다.
