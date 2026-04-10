# Docs response_origin nullable truth sync verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-response-origin-nullable-truth-sync-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work` `work/4/9/2026-04-09-docs-response-origin-nullable-truth-sync.md`가 이전 verification note가 고정한 top-level `response_origin` nullability drift를 실제로 닫았는지 다시 확인하고, 같은 response payload docs family의 다음 단일 current-risk reduction 슬라이스를 좁힐 필요가 있었습니다.
- 같은 날짜의 기존 verification note `verify/4/9/2026-04-09-docs-approval-reason-record-reject-reissue-truth-sync-verification.md`를 먼저 읽은 뒤, 그 후속 `/work`가 실제로 그 지적을 어디까지 닫았는지 재검수했습니다.

## 핵심 변경
- 최신 `/work`는 targeted top-level payload wording에 대해서는 truthful합니다. `docs/PRODUCT_SPEC.md:310`, `docs/ARCHITECTURE.md:155`, `docs/ACCEPTANCE_CRITERIA.md:93`는 이제 shipped response payload contract와 맞습니다.
  - `app/serializers.py:53`은 response payload에 `response_origin`을 항상 직렬화하고, `_serialize_response_origin(...)`은 origin 부재 시 `None`을 반환합니다 (`app/serializers.py:333-345`).
  - 셸도 nullable payload를 그대로 소비합니다 (`app/static/app.js:3153`, `app/static/app.js:3196`).
- 다만 `/work`의 `남은 리스크 없음 — response_origin nullability 진실 동기화 완료`까지는 아직 과장입니다. nested `original_response_snapshot.response_origin` contract는 현재 구현에서 여전히 nullable입니다.
  - `core/agent_loop.py:220`은 snapshot의 `response_origin`을 `dict(...)` 또는 `None`으로 저장합니다.
  - `app/serializers.py:358`은 snapshot 안의 `response_origin`도 같은 serializer helper로 직렬화합니다.
  - `tests/test_smoke.py:2725`는 `response.original_response_snapshot["response_origin"] is None`을 직접 잠급니다.
- 그런데 authoritative docs는 이 nested contract를 아직 명시적으로 닫지 않았습니다.
  - `docs/PRODUCT_SPEC.md:318`은 `original_response_snapshot` 필드 목록만 적고 nested `response_origin` nullability를 드러내지 않습니다.
  - `docs/PRODUCT_SPEC.md:459`, `docs/PRODUCT_SPEC.md:524`, `docs/ARCHITECTURE.md:368`은 snapshot의 `response_origin`을 message-level shape(`{provider, badge, label, model, kind, answer_mode, source_roles, verification_label}`)로만 적어 object-only처럼 읽힐 수 있습니다.
  - `docs/ACCEPTANCE_CRITERIA.md:103`도 snapshot field가 message-level shape를 재사용한다고만 적어, nested `response_origin`의 `null` 가능성을 직접 드러내지 않습니다.
- 반대로 `docs/PRODUCT_SPEC.md:257`과 `docs/ARCHITECTURE.md:205`는 이번 다음 슬라이스 대상이 아닙니다. 그 위치는 session-message optional field 설명이고, shipped session message는 `response_origin`이 없으면 필드 자체를 생략하기 때문입니다 (`core/agent_loop.py:7367-7368`; `tests/test_web_app.py:6197-6198`).
- 다음 Claude 슬라이스는 `.pipeline/claude_handoff.md`에 `Docs PRODUCT_SPEC ARCHITECTURE ACCEPTANCE_CRITERIA original_response_snapshot response_origin nullable truth sync`로 고정했습니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,240p' work/4/9/2026-04-09-docs-response-origin-nullable-truth-sync.md`
- `sed -n '1,240p' verify/4/9/2026-04-09-docs-approval-reason-record-reject-reissue-truth-sync-verification.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `sed -n '1,220p' docs/MILESTONES.md`
- `sed -n '1,220p' docs/TASK_BACKLOG.md`
- `git status --short`
- `git diff -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
- `git diff --check`
- `rg -n '\\bresponse_origin\\b|original_response_snapshot' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md app/serializers.py core/agent_loop.py app/static/app.js tests/test_web_app.py tests/test_smoke.py -S`
- `rg -n '\\bresponse_origin\\b' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md -S`
- `rg -n 'original_response_snapshot\\[\"response_origin\"\\]|assertIsNone\\(.*original_response_snapshot\\[\"response_origin\"\\]|assertNotIn\\(\"response_origin\"' tests/test_web_app.py tests/test_smoke.py -S`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '248,266p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '300,340p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '452,466p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '516,528p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '145,175p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '198,210p'`
- `nl -ba docs/ARCHITECTURE.md | sed -n '360,372p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '86,110p'`
- `nl -ba app/serializers.py | sed -n '1,70p'`
- `nl -ba app/serializers.py | sed -n '80,115p'`
- `nl -ba app/serializers.py | sed -n '347,365p'`
- `nl -ba core/agent_loop.py | sed -n '209,228p'`
- `nl -ba core/agent_loop.py | sed -n '7360,7380p'`
- `nl -ba core/agent_loop.py | sed -n '7427,7442p'`
- `nl -ba tests/test_smoke.py | sed -n '2718,2727p'`
- `nl -ba tests/test_web_app.py | sed -n '4488,4504p'`
- `nl -ba tests/test_web_app.py | sed -n '4572,4582p'`
- `nl -ba tests/test_web_app.py | sed -n '6188,6199p'`
- `nl -ba tests/test_web_app.py | sed -n '9614,9646p'`
- `ls -1 verify/4/9`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `sed -n '1,220p' .pipeline/gemini_request.md`
- `sed -n '1,220p' .pipeline/operator_request.md`

## 남은 리스크
- 이번 라운드는 docs/code truth 대조와 handoff 갱신만 수행했습니다. Python unit test와 Playwright는 재실행하지 않았습니다.
- top-level response payload `response_origin` wording은 맞춰졌지만, `original_response_snapshot.response_origin` nullable wording은 아직 authoritative docs에서 직접 닫히지 않았습니다.
- 현재 worktree에는 이 라운드와 무관한 dirty/untracked 파일이 많이 남아 있으므로 다음 슬라이스도 unrelated changes를 건드리지 말아야 합니다.
