# 선택지형 operator stop advisory-first 라우팅 보강

## 변경 파일
- `pipeline_runtime/operator_autonomy.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.claude/rules/pipeline-runtime.md`
- `work/README.md`
- `verify/README.md`
- `work/4/21/2026-04-21-menu-choice-advisory-routing.md`

## 사용 skill
- `security-gate`
- `doc-sync`
- `work-log-closeout`

## 변경 이유
- 문자/숫자/한글 라벨 선택지가 뜬 operator stop이 실제 안전 정지가 아니라 계획서, milestone, 최신 `/work`, 최신 `/verify` 근거로 에이전트끼리 먼저 좁힐 수 있는 경우에도 `approval_required`처럼 표면화되어 사람 대기로 보이는 문제가 있었습니다.
- 반복 멈춤을 줄이기 위해 선택지형 stop은 런타임 분류 경계에서 `slice_ambiguity` 성격의 verify/handoff follow-up으로 낮추고, safety/destructive/auth/credential/approval-record/truth-sync blocker만 operator stop으로 남기도록 보강했습니다.

## 핵심 변경
- `operator_autonomy.classify_operator_candidate(...)`가 `gate_24h` 후보 중 문자/숫자/한글 라벨 선택지 메뉴를 감지하면 `reason_code=slice_ambiguity`, `decision_class=next_slice_selection`, `routed_to=codex_followup`으로 분류합니다.
- 감지 범위는 문자형(`A/B/C`), 숫자형(`1.`, `1)`, `1:`), 한글형(`1안`, `2번`, `선택지 1/2/3`), circled digit(`①/②`), 괄호형 inline 라벨(`(B)`, `(C)`, `(D)`) 계열입니다. 숫자 inline set은 경로나 날짜 오인을 줄이기 위해 선택 의도 단어가 있을 때만 인정합니다.
- blocker marker 판정은 전체 control prose가 아니라 `DECISION_REQUIRED` 같은 결정 헤더 중심으로 좁혔습니다. 본문 설명에 `approval_record/auth/credential` marker가 등장해도 그것만으로 실제 operator blocker로 보지 않습니다.
- `approval_record`, safety, destructive, auth/credential, truth-sync 같은 blocker marker가 있으면 선택지 메뉴여도 기존 `pending_operator` 경계를 유지합니다.
- supervisor 회귀 테스트에 선택지형 menu가 advisory follow-up으로 내려가는 케이스와 approval-record blocker가 operator stop으로 남는 케이스를 추가했습니다.
- watcher 회귀 테스트에 실제 `.pipeline/operator_request.md` 선택지 menu가 `codex_followup`으로 해석되는 replay를 추가했습니다.
- `.pipeline` 및 AGENTS/CLAUDE/GEMINI/PROJECT/work/verify 문서에 “선택지형 stop은 advisory-first, 진짜 blocker만 operator stop” 규칙을 동기화했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/operator_autonomy.py`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_choice_menu_routes_to_advisory_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_choice_menu_keeps_approval_record_blocker tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_branch_commit_gate_stays_followup_visible tests.test_operator_request_schema`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_choice_menu_routes_to_advisory_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_numbered_choice_menu_routes_to_advisory_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_choice_menu_keeps_approval_record_blocker tests.test_watcher_core.TurnResolutionTest.test_choice_menu_operator_request_routes_to_followup tests.test_watcher_core.TurnResolutionTest.test_numbered_choice_menu_operator_request_routes_to_followup`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_inline_parenthesized_choices_route_to_advisory_followup tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_body_marker_docs_do_not_block_choice_menu tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_classify_operator_candidate_choice_menu_keeps_approval_record_blocker tests.test_watcher_core.TurnResolutionTest.test_parenthesized_inline_choice_operator_request_routes_to_followup tests.test_watcher_core.TurnResolutionTest.test_choice_menu_operator_request_ignores_explanatory_body_blocker_markers`
- 현재 `.pipeline/operator_request.md` 직접 분류 결과: `mode=triage`, `reason_code=slice_ambiguity`, `decision_class=next_slice_selection`, `routed_to=codex_followup`.
- `python3 -m unittest tests.test_pipeline_runtime_control_writers`
- `python3 -m unittest tests.test_watcher_core.WatcherDispatchQueueControlMismatchTest.test_choice_menu_operator_request_routes_to_followup tests.test_pipeline_runtime_control_writers`는 잘못된 class 경로로 `AttributeError`가 나서 실패했습니다.
- `python3 -m unittest tests.test_watcher_core.TurnResolutionTest.test_choice_menu_operator_request_routes_to_followup tests.test_pipeline_runtime_control_writers`
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` (`Ran 110 tests`, OK)
- `python3 -m unittest tests.test_watcher_core` (`Ran 153 tests`, OK)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` (`Ran 111 tests`, OK)
- `python3 -m unittest tests.test_watcher_core` (`Ran 154 tests`, OK)
- `python3 -m unittest tests.test_operator_request_schema tests.test_pipeline_runtime_control_writers` (`Ran 15 tests`, OK, skipped 1)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor` (`Ran 113 tests`, OK)
- `python3 -m unittest tests.test_watcher_core` (`Ran 156 tests`, OK)
- 현재 `.pipeline/operator_request.md`를 새 분류기로 직접 분류했을 때 `mode=triage`, `reason_code=slice_ambiguity`, `decision_class=next_slice_selection`, `routed_to=codex_followup` 확인.
- `git diff --check -- pipeline_runtime/operator_autonomy.py tests/test_pipeline_runtime_supervisor.py .pipeline/README.md AGENTS.md PROJECT_CUSTOM_INSTRUCTIONS.md CLAUDE.md GEMINI.md .claude/rules/pipeline-runtime.md work/README.md verify/README.md`
- `python3 -m pipeline_runtime.cli restart /home/xpdlqj/code/projectH --no-attach`
- 재시작 후 runtime status: `RUNNING`, `turn_state=VERIFY_ACTIVE`, `autonomy.mode=normal`.

## 남은 리스크
- full supervisor / watcher 전체 suite는 이번 focused runtime-classification 변경 범위 밖이라 실행하지 않았습니다.
- 선택지 menu 감지는 흔한 문자/숫자/한글/괄호형 라벨 포맷을 지원하지만, 문장형 자연어 선택지처럼 라벨이 전혀 없는 포맷은 아직 안전하게 감지하지 않습니다.
