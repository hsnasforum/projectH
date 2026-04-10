# docs: response-origin summary richness family closure history-card claim progress handoff verification

## 변경 파일
- `verify/4/9/2026-04-09-docs-response-origin-summary-richness-family-closure-history-card-claim-progress-handoff-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`가 `response-origin summary richness` docs family closure만 주장한 상태이므로, 그 주장이 여전히 truthful한지 다시 확인하고 다음 `CONTROL_SEQ: 13` 구현 슬라이스를 하나로 좁혀야 했습니다.
- 기존 `CONTROL_SEQ: 12` handoff는 history-card progress surfacing 방향 자체는 맞았지만, 현재 코드 기준으로 `app/static/app.js` 렌더링만이 아니라 `session.web_search_history` 직렬화 누락도 함께 닫아야 truthful한 end-to-end slice가 됩니다.

## 핵심 변경
- 최신 `/work`의 direct claim은 여전히 truthful합니다.
  - `docs/PRODUCT_PROPOSAL.md:58`
  - `docs/project-brief.md:15`
  - `docs/project-brief.md:82`
- `git diff --check` 기준 공백 오류는 없고, latest `/work`가 다룬 docs closure를 뒤집는 새 diff는 확인되지 않았습니다.
- 다음 exact slice는 Gemini의 broad advice `claim-based entity-card shaping`를 현재 트리 기준으로 더 좁힌 one coherent bundle로 확정할 수 있습니다.
  - stored web-search record와 summary layer는 이미 `claim_coverage_progress_summary`를 보존합니다.
    - `storage/web_search_store.py:241`
    - `storage/web_search_store.py:317`
  - response/session/current detail surface는 이미 이 필드를 직렬화·표시합니다.
    - `app/serializers.py:63`
    - `app/serializers.py:213`
    - `app/serializers.py:328`
    - `app/static/app.js:3165`
    - `app/static/app.js:3211`
  - 하지만 history-card payload는 아직 이 필드를 브라우저로 내리지 않아 end-to-end surfacing이 닫히지 않았습니다.
    - `app/serializers.py:261`
    - `app/serializers.py:268`
    - `app/serializers.py:296`
  - 현재 dirty worktree에는 `app/static/app.js`에만 progress summary를 card meta에 붙이는 미완료 diff가 이미 존재합니다.
    - `git diff -- app/static/app.js`
    - 이 변경은 latest `/work`에 기록되지 않았으므로, 다음 Claude 라운드는 이를 되돌리지 말고 직렬화·테스트·문서 sync까지 함께 닫아야 합니다.
- 따라서 `CONTROL_SEQ: 13` handoff는 `app.web history-card claim-progress summary end-to-end surfacing`으로 갱신했습니다.
  - 범위: `app/serializers.py` + `app/static/app.js` + focused regression/tests + required doc sync
  - 제외: claim-coverage selection logic, response detail panel semantics, pipeline/controller/setup tooling

## 검증
- `sed -n '1,260p' work/4/9/2026-04-09-docs-response-origin-summary-richness-family-closure.md`
- `sed -n '1,260p' verify/4/9/2026-04-09-docs-response-origin-summary-richness-family-closure-verification.md`
- `sed -n '1,220p' report/gemini/2026-04-09-docs-to-ui-shaping-arbitration.md`
- `git status --short`
- `git diff --check`
- `sed -n '1,260p' docs/MILESTONES.md`
- `sed -n '1,260p' docs/TASK_BACKLOG.md`
- `sed -n '1,220p' docs/NEXT_STEPS.md`
- `rg -n "claim_coverage_progress_summary|claim_coverage_summary|history-card|history card|search-history" app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs core app`
- `nl -ba app/static/app.js | sed -n '2952,2975p;3158,3218p'`
- `nl -ba app/serializers.py | sed -n '1,140p;200,340p'`
- `nl -ba storage/web_search_store.py | sed -n '200,330p'`
- `nl -ba tests/test_web_app.py | sed -n '5268,5455p;14780,14905p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1232,1298p'`
- `nl -ba README.md | sed -n '76,82p;136,140p'`
- `nl -ba docs/PRODUCT_SPEC.md | sed -n '334,364p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '37,45p;88,106p'`
- Python unit test와 Playwright는 이번 verify 라운드에서 재실행하지 않았습니다. 최신 `/work`가 docs-only closure 확인 라운드였고, 이번 라운드는 next slice truth narrowing과 control-slot 갱신이 목적이었기 때문입니다.

## 남은 리스크
- repo worktree가 크게 dirty하며, 현재 task와 직접 맞닿는 미완료 변경은 `app/static/app.js`에만 있습니다. 다음 구현 라운드는 이 diff를 되돌리지 말고 실제 payload 직렬화와 검증까지 닫아야 합니다.
- history-card progress summary는 아직 shipped contract가 아닙니다. `app/serializers.py` 누락 때문에 현재 브라우저 세션 payload만으로는 card meta에 안정적으로 노출되지 않습니다.
- stale lower-seq control files(`.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `.pipeline/operator_request.md`, prior `.pipeline/claude_handoff.md`)는 남아 있지만, newest-valid-control 판정은 새 `CONTROL_SEQ: 13` handoff가 담당합니다.
