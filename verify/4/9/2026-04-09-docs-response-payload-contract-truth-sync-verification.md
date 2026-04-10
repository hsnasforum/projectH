# Docs response payload contract truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-response-payload-contract-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-response-payload-contract-truth-sync.md`가 추가한 response payload contract 문서가 현재 코드, 셸 소비 경로, 테스트와 실제로 맞는지 다시 확인하고 다음 단일 슬라이스를 고정할 필요가 있었습니다.
- 오늘 날짜 `verify/4/9/`에는 기존 verification note가 없어서 이번 재검수 결과를 새 note로 남깁니다.

## 핵심 변경
- 최신 `/work`의 큰 방향은 맞습니다. `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`에 response payload contract 섹션이 실제로 존재하고, 8개 shell control fields(`status`, `actions_taken`, `requires_approval`, `proposed_note_path`, `saved_note_path`, `web_search_record_path`, `follow_up_suggestions`, `search_results`)도 현재 셸/테스트 의존 경로와 맞게 요약되어 있습니다.
- 다만 이 family는 아직 완전히 닫히지 않았습니다. `docs/PRODUCT_SPEC.md:288`와 `docs/ARCHITECTURE.md:139`가 `status` 예시 값으로 `completed`를 적고 있는데, 현재 canonical enum은 `core/contracts.py:16-20`의 `answer`, `error`, `needs_approval`, `saved` 네 값뿐입니다.
- `core/agent_loop.py`도 실제 응답에서 `ResponseStatus.ANSWER`, `ResponseStatus.ERROR`, `ResponseStatus.NEEDS_APPROVAL`, `ResponseStatus.SAVED`만 사용합니다.
- focused tests 역시 같은 현재 상태값을 잠그고 있습니다. 예: `tests/test_smoke.py:185`, `tests/test_smoke.py:2713`, `tests/test_smoke.py:3189`, `tests/test_web_app.py:756`, `tests/test_web_app.py:5865`, `tests/test_web_app.py:673`.
- 현재 트리에서 `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`는 비어 있어서 `/work`가 적은 과거 `89줄 추가` 수치는 지금 상태만으로는 재현되지 않습니다. 이번 검수는 현재 landed content와 현재 코드/테스트 참조를 기준으로 truth를 판정했습니다.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA response status enum truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-response-payload-contract-truth-sync.md`
- `sed -n '1,260p' verify/4/8/2026-04-08-docs-task-log-session-delete-preference-action-truth-sync-verification.md`
- `ls -1 verify/4/9 2>/dev/null || true`
- `sed -n '1,260p' docs/NEXT_STEPS.md`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `nl -ba app/serializers.py | sed -n '1,180p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '283,325p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '132,176p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '114,124p'`
- `nl -ba core/contracts.py | sed -n '1,80p'`
- `rg -n 'applied_preferences|follow_up_suggestions|search_results|saved_note_path|proposed_note_path|requires_approval|status|actions_taken|web_search_record_path|selected_source_paths' app/static/app.js -S`
- `rg -n 'ResponseStatus\\.(ANSWER|ERROR|NEEDS_APPROVAL|SAVED)|class ResponseStatus' core/contracts.py core/agent_loop.py -S`
- `rg -n 'response\\]\\[\"status\"\\]|response\\.status' tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n '\`status\`.*completed|response status \\(\`needs_approval\`, \`completed\`\\)|\`completed\`' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md -S`

## 남은 리스크
- 이번 라운드는 docs truth 대조와 handoff 갱신만 수행했습니다. Python unit test나 Playwright는 재실행하지 않았습니다.
- response payload family의 큰 문서화는 landed 상태지만, 실제 enum 값은 아직 다음 docs-only 슬라이스에서 바로잡아야 합니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
