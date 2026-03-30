## Claude에게 전달할 지시사항

다음 라운드에서는 `/api/aggregate-transition-conflict-check`의 HTTP handler dispatch만 focused regression으로 추가해 주세요. current code/docs/e2e/service truth는 이미 conflict visibility까지 맞으므로, behavior widening 없이 handler 경로 한 층만 고정하면 됩니다.

반드시 먼저 읽을 파일:
- `verify/3/30/2026-03-30-conflict-visibility-service-regression-verification.md`
- `work/3/30/2026-03-30-conflict-visibility-service-regression.md`
- `AGENTS.md`
- `CLAUDE.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `app/web.py`
- `tests/test_web_app.py`

dirty worktree 경고:
- 현재 worktree가 넓게 더럽습니다. unrelated 변경은 절대 되돌리거나 섞지 마세요.
- current truth는 최신 `/work`와 최신 `/verify`를 우선하세요.

목표:
- `LocalAssistantHandler` 기준 `/api/aggregate-transition-conflict-check` POST dispatch가 `service.check_aggregate_conflict_visibility(...)`로 연결되는지 focused handler-level regression으로 고정
- 가능하면 response JSON에 최소한 아래 핵심 truth가 보존되는지 확인
  - `ok = true`
  - `canonical_transition_id`
  - `conflict_visibility_record.transition_action = future_reviewed_memory_conflict_visibility`

정확한 범위 제한:
- reviewed-memory behavior, route semantics, UI copy, docs wording은 바꾸지 마세요
- `future_reviewed_memory_conflict_visibility` 위 새 기능을 열지 마세요
- repeated-signal promotion, broader durable promotion, cross-session counting, user-level memory는 건드리지 마세요
- 가능하면 `tests/test_web_app.py`만 수정하고, app code는 테스트 보조가 정말 필요할 때만 최소로 건드리세요
- e2e는 건드리지 마세요

필수 검증:
- `python3 -m py_compile app/web.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app`
- `git diff --check`

마무리:
- `/work` closeout을 남기세요
- 응답은 한국어 존댓말로 작성하세요
