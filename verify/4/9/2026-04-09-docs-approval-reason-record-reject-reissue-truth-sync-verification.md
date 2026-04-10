# Docs approval_reason_record reject-reissue truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-approval-reason-record-reject-reissue-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-approval-reason-record-reject-reissue-truth-sync.md`가 이전 verification note가 지적한 `approval_reason_record` 범위 drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 고정할 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-response-status-enum-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 truthful합니다. `docs/PRODUCT_SPEC.md:200`, `docs/PRODUCT_SPEC.md:320`, `docs/ARCHITECTURE.md:163`, `docs/ARCHITECTURE.md:290` 모두 `approval_reason_record`를 reject / reissue 양쪽에 대해 설명하도록 수정되어, 이전 verification note가 지적한 reissue-only wording drift는 닫혔습니다.
- 이 내용은 실제 구현과도 맞습니다. `core/agent_loop.py:7229-7283`은 reissue 응답에 `approval_reason_record`를 싣고, `core/agent_loop.py:7303-7333`은 reject 응답에도 같은 필드를 싣습니다.
- focused tests도 양쪽 경로를 잠급니다. 예: `tests/test_web_app.py:6391-6396`(reissue), `tests/test_web_app.py:7112-7117`와 `tests/test_smoke.py:2988-2994`(reject).
- 다만 response payload docs family는 아직 완전히 닫히지 않았습니다. `response_origin`은 serializer에서 `null`이 될 수 있고 셸도 `null`을 그대로 소비하지만, authoritative docs 일부는 아직 object 고정처럼 읽힙니다.
  - `app/serializers.py:53`은 `response_origin`을 `_serialize_response_origin(response.response_origin)`으로 그대로 직렬화하고, `_serialize_response_origin`은 `origin is None`이면 `None`을 반환합니다 (`app/serializers.py:333-345`).
  - `core/agent_loop.py:80`에서 `AgentResponse.response_origin` 기본값은 `None`입니다.
  - 일부 오류 경로는 실제로 `response_origin` 없이 응답을 만듭니다. 예: `core/agent_loop.py:391-395`, `core/agent_loop.py:399-403`, `core/agent_loop.py:8775-8794`.
  - 셸도 nullable contract를 전제로 렌더링합니다. `app/static/app.js:3153`, `app/static/app.js:3196`은 `response_origin || null`을 넘기고, 비어 있으면 `renderResponseOrigin(null)`도 직접 호출합니다 (`app/static/app.js:3170`).
  - 그런데 현재 docs는 아직 `response_origin`을 object shape로만 적습니다. 예: `docs/PRODUCT_SPEC.md:310`, `docs/ARCHITECTURE.md:155`, `docs/ACCEPTANCE_CRITERIA.md:93`.
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA response_origin nullable truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,260p' work/4/9/2026-04-09-docs-approval-reason-record-reject-reissue-truth-sync.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-response-status-enum-truth-sync-verification.md`
- `ls -1 verify/4/9`
- `git status --short`
- `git diff --check`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '194,204p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '316,322p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '161,165p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '284,292p'`
- `rg -n 'reissued approvals|reissue reason record|rejected or reissued approvals|reject or reissue reason record' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `sed -n '1,260p' docs/NEXT_STEPS.md`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `rg -n '\`response_origin\`|response_origin' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'response_origin\\s*=|AgentResponse\\(|response_origin:' core/agent_loop.py app/web.py app/serializers.py -S`
- `nl -ba core/agent_loop.py | sed -n '60,120p'`
- `nl -ba core/agent_loop.py | sed -n '220,240p'`
- `nl -ba core/agent_loop.py | sed -n '388,460p'`
- `nl -ba core/agent_loop.py | sed -n '7340,7388p'`
- `nl -ba core/agent_loop.py | sed -n '8770,8800p'`
- `nl -ba app/serializers.py | sed -n '31,60p'`
- `nl -ba app/serializers.py | sed -n '333,345p'`
- `rg -n 'renderResponseOrigin\\(|response_origin \\|\\| null|data\\.response\\?\\.response_origin \\|\\| null' app/static/app.js app/frontend/src -S`
- `nl -ba app/static/app.js | sed -n '3148,3200p'`
- `nl -ba tests/test_web_app.py | sed -n '6389,6396p'`
- `nl -ba tests/test_web_app.py | sed -n '7108,7118p'`
- `nl -ba tests/test_web_app.py | sed -n '660,690p'`
- `nl -ba tests/test_web_app.py | sed -n '4640,4695p'`
- `nl -ba tests/test_smoke.py | sed -n '2987,2994p'`
- `nl -ba tests/test_smoke.py | sed -n '3178,3194p'`

## 남은 리스크
- 이번 라운드는 docs truth 대조와 handoff 갱신만 수행했습니다. Python unit test나 Playwright는 재실행하지 않았습니다.
- `response_origin` nullability는 현재 serializer/agent/shell contract에 존재하지만 authoritative docs 일부는 아직 object-only처럼 읽힐 수 있어, 다음 docs-only 슬라이스에서 명시적으로 바로잡는 편이 맞습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
