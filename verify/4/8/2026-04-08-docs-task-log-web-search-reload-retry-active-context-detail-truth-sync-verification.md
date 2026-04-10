# Docs task-log web-search reload-retry-active-context detail truth sync verification

## 변경 파일

- `verify/4/8/2026-04-08-docs-task-log-web-search-reload-retry-active-context-detail-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill

- `round-handoff`

## 변경 이유

최신 `/work`가 문서화한 web-search reload/retry/follow-up task-log detail이 실제 구현과 맞는지 재확인하고, 같은 task-log docs family에서 남은 가장 작은 current-risk slice를 다음 Claude handoff로 고정할 필요가 있었습니다.

## 핵심 변경

- 최신 `/work`의 문서 수정 자체는 맞았습니다.
- `docs/ARCHITECTURE.md:215-217`은 실제로 `web_search_record_loaded`, `web_search_retried`, `answer_with_active_context`의 exact detail shape를 적고 있었고, 이는 `core/agent_loop.py:6124-6134`, `core/agent_loop.py:6344-6352`, `core/agent_loop.py:6779-6791`의 logger와 일치했습니다.
- `docs/PRODUCT_SPEC.md:118`과 `docs/ACCEPTANCE_CRITERIA.md:112`도 web-search/follow-up action family가 ARCHITECTURE의 full detail shape를 참조한다는 수준으로 truthfully 갱신돼 있었습니다.
- 다만 최신 `/work`의 `남은 리스크`에 적힌 “task-log action detail shape 문서화가 모든 주요 user-visible action family에서 완료됨”은 과했습니다.
- 아직 `docs/ARCHITECTURE.md:211-214`에는 `stream_cancel_requested`, `web_search_permission_updated`, `permissions_updated`, `ocr_not_supported`가 이름만 남아 있고, 실제 구현은 `app/handlers/chat.py:56-59`, `app/handlers/chat.py:190-193`, `core/agent_loop.py:8706-8709`, `core/agent_loop.py:8781-8787`에서 exact detail shape를 이미 고정하고 있습니다.
- 이 action들은 current MVP의 user-visible flow와 직접 연결돼 있습니다. `AGENTS.md:38-40`, `README.md:55`, `README.md:66`, `README.md:68`, `docs/NEXT_STEPS.md:13-15`, `docs/MILESTONES.md:7`, `docs/MILESTONES.md:33`, `docs/MILESTONES.md:99`, `docs/TASK_BACKLOG.md:7`, `docs/TASK_BACKLOG.md:22`, `tests/test_smoke.py:7554`, `tests/test_web_app.py:6011-6052`, `app/templates/index.html:119`, `app/static/app.js:549-553`, `app/static/app.js:733-753`이 각각 streaming cancel, permission-gated web investigation, OCR-not-supported guidance를 현재 shipped contract로 다룹니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ACCEPTANCE_CRITERIA ARCHITECTURE task-log stream-cancel-permission-update-ocr detail truth sync`로 고정했습니다.

## 검증

- `sed -n '1,260p' work/4/8/2026-04-08-docs-task-log-web-search-reload-retry-active-context-detail-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-task-log-candidate-confirmation-review-detail-field-shape-truth-sync-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '112,120p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '111,113p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '209,224p'`
- `nl -ba core/agent_loop.py | sed -n '6120,6135p;6343,6353p;6779,6791p;8700,8710p;8774,8788p'`
- `nl -ba app/handlers/chat.py | sed -n '54,60p;188,194p'`
- `rg -n "streaming cancel|streaming progress|OCR-not-supported|OCR|permission-gated web investigation|disabled/approval/enabled per session|stream_cancel_requested|web_search_permission_updated|permissions_updated|ocr_not_supported" README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/TASK_BACKLOG.md AGENTS.md -S`
- `rg -n "cancelled|cancel" tests/test_web_app.py tests/test_smoke.py app/static/app.js app/templates/index.html -S`
- `rg -n "stream_cancel_requested|web_search_permission_updated|permissions_updated|ocr_not_supported" tests/test_web_app.py tests/test_smoke.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md -S`
- `git diff -- docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
- `git diff --check`
- `git status --short`

## 남은 리스크

- task-log docs family 안에는 아직 `stream_cancel_requested`, `web_search_permission_updated`, `permissions_updated`, `ocr_not_supported`, `request_received`, `request_cancelled`, `document_context_updated`, reviewed-memory transition actions의 exact detail shape omission이 남아 있습니다.
- 이번 라운드는 문서/코드 truth 대조와 dirty-worktree 확인만 다시 실행했습니다. 새 unit test나 Playwright는 다시 실행하지 않았습니다.
