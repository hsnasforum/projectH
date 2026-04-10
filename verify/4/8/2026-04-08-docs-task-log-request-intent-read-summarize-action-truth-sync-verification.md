# Docs task-log request-intent-read-summarize action truth sync verification

## 변경 파일

- `verify/4/8/2026-04-08-docs-task-log-request-intent-read-summarize-action-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work`의 document-loop task-log action 문서화가 실제 코드와 맞는지 다시 확인하고, 같은 task-log docs family에서 남은 가장 작은 current-risk slice를 다음 Claude handoff로 고정할 필요가 있었습니다.

## 핵심 변경

- 최신 `/work`의 실제 수정은 대부분 맞았지만, 완전히 truthful하지는 않았습니다.
- `docs/PRODUCT_SPEC.md:118`과 `docs/ACCEPTANCE_CRITERIA.md:112`은 실제로 document-loop action family(`request_intent_classified`, `read_search_results`, `summarize_search_results`, `read_uploaded_file`, `summarize_uploaded_file`, `read_file`, `summarize_file`)를 top task-log wording에 추가했고, 이는 현재 shipped document-first loop와 맞습니다.
- `docs/ARCHITECTURE.md:200-205`의 `read_search_results`, `summarize_search_results`, `read_uploaded_file`, `summarize_uploaded_file`, `read_file`, `summarize_file` detail shape도 `core/agent_loop.py:7904-7920`, `core/agent_loop.py:7956-7962`, `core/agent_loop.py:8127-8137`, `core/agent_loop.py:8183-8189`, `core/agent_loop.py:8311-8320`, `core/agent_loop.py:8367-8373`와 일치했습니다.
- 다만 `docs/ARCHITECTURE.md:199`의 `request_intent_classified` detail은 아직 코드와 완전히 맞지 않습니다. 문서는 `{kind, query, score, reasons, freshness_risk, answer_mode, suggestion_kind, suggestion_query, suggestion_score, suggestion_reasons, suggestion_freshness_risk}`까지만 적고 있지만, 실제 코드는 `core/agent_loop.py:7556-7572`에서 여기에 더해 `suggestion_answer_mode`도 함께 기록합니다.
- 따라서 `/work`의 `모든 주요 ... family에서 detail shape 문서화 완료` 결론은 과했습니다. same-family의 더 작은 parity gap이 아직 남아 있습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs ARCHITECTURE request_intent_classified suggestion field parity truth sync`로 고정했습니다.

## 검증

- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/8/2026-04-08-docs-task-log-request-intent-read-summarize-action-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-task-log-request-received-cancelled-context-update-detail-truth-sync-verification.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '116,120p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '111,113p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '195,232p'`
- `nl -ba core/agent_loop.py | sed -n '7556,7574p;7904,7963p;8127,8189p;8311,8373p'`
- `rg -n "request_intent_classified|read_search_results|summarize_search_results|read_uploaded_file|summarize_uploaded_file|read_file|summarize_file|session_deleted|all_sessions_deleted|agent_error|request_received|request_cancelled|document_context_updated|web_search_record_loaded|web_search_retried|answer_with_active_context" docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md README.md core/agent_loop.py app/web.py -S`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
- `git diff --check`
- `git status --short`

## 남은 리스크

- 현재 same-family current-risk는 `docs/ARCHITECTURE.md`의 `request_intent_classified` detail에서 `suggestion_answer_mode`가 빠진 parity gap입니다.
- 이번 라운드는 문서/코드 truth 대조와 dirty-worktree 확인만 다시 실행했습니다. 새 unit test나 Playwright는 다시 실행하지 않았습니다.
