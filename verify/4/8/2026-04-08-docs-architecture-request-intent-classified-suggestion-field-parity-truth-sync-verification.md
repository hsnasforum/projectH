# Docs ARCHITECTURE request_intent_classified suggestion field parity truth sync verification

## 변경 파일

- `verify/4/8/2026-04-08-docs-architecture-request-intent-classified-suggestion-field-parity-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work`의 `request_intent_classified` parity 수정이 실제 코드와 맞는지 다시 확인하고, 같은 task-log docs family에서 남은 가장 작은 current-risk slice를 다음 Claude handoff로 고정할 필요가 있었습니다.

## 핵심 변경

- 최신 `/work`는 truthful했습니다.
- `docs/ARCHITECTURE.md:199`는 실제로 `request_intent_classified` detail에 `suggestion_answer_mode`를 추가했고, 이는 `core/agent_loop.py:7556-7572`의 current logger shape와 정확히 일치합니다.
- 이전 `/verify`에서 지적했던 same-family parity gap은 이번 슬라이스로 닫혔고, `/work`의 `모든 주요 action family에서 detail shape 문서화 완료` 결론도 현재 기준에서는 과장으로 보이지 않았습니다.
- 다만 same-family current-risk가 완전히 0은 아닙니다. root task-log docs에는 아직 `agent_error`가 빠져 있지만, 실제 구현은 `core/agent_loop.py:8789-8798`에서 fallback error response와 함께 `action=\"agent_error\"`, `detail={\"error\": str(exc)}`를 기록합니다.
- tie-break는 같은 family 안의 user-visible current-risk를 우선했습니다. `session_deleted` / `all_sessions_deleted`와 system-level preference actions도 문서에는 없지만, `agent_error`가 현재 visible error response path와 더 직접 연결됩니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA ARCHITECTURE task-log agent_error action truth sync`로 고정했습니다.

## 검증

- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-docs-architecture-request-intent-classified-suggestion-field-parity-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-task-log-request-intent-read-summarize-action-truth-sync-verification.md`
- `sed -n '1,120p' docs/NEXT_STEPS.md`
- `sed -n '1,120p' docs/MILESTONES.md`
- `sed -n '1,120p' docs/TASK_BACKLOG.md`
- `nl -ba docs/ARCHITECTURE.md | sed -n '195,205p'`
- `nl -ba core/agent_loop.py | sed -n '7556,7574p;8788,8800p'`
- `nl -ba app/web.py | sed -n '120,145p'`
- `nl -ba tests/test_web_app.py | sed -n '660,690p;6858,6872p;7018,7032p'`
- `nl -ba tests/test_smoke.py | sed -n '3178,3194p;3349,3366p'`
- `rg -n "session_deleted|all_sessions_deleted|agent_error|preference_activated|preference_paused|preference_rejected" docs README.md app/static app/templates tests app/web.py core/agent_loop.py app/handlers -S`
- `git diff -- docs/ARCHITECTURE.md`
- `git diff --check`
- `git status --short`

## 남은 리스크

- 같은 task-log docs family에서 남은 가장 작은 current-risk는 current visible error fallback path에 연결된 `agent_error` omission입니다.
- `session_deleted` / `all_sessions_deleted`와 system-level preference actions도 여전히 docs 밖에 있지만, 이번 handoff에서는 user-visible relevance가 더 큰 `agent_error`를 우선했습니다.
- 이번 라운드는 문서/코드 truth 대조와 dirty-worktree 확인만 다시 실행했습니다. 새 unit test나 Playwright는 다시 실행하지 않았습니다.
