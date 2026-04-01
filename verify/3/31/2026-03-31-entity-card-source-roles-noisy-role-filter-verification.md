# 2026-03-31 entity-card source_roles noisy role filter verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-source-roles-noisy-role-filter-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-source-roles-noisy-role-filter.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 same-family follow-up으로 entity-card `source_roles` badge/meta에서 noisy single-source role leakage를 막는 `core/agent_loop.py` 최소 fix와 `tests/test_web_app.py` 회귀 보강을 주장하므로, 이번 검수에서는 그 코드 변경이 실제로 들어갔는지, 새 assertion이 실제 경로를 덮는지, docs 무변경이 아직 truthful한지, 그리고 필요한 최소 검증만 재실행하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 코드 변경은 실제로 반영되어 있습니다. [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5051) 의 `_build_web_search_origin`은 `answer_mode == "entity_card"`일 때 `_extract_entity_source_fact_bullets()`를 통과한 source만 `source_roles` 산출에 쓰고, 모두 탈락하면 원래 source 목록으로 fallback 하도록 바뀌었습니다. 따라서 entity-card badge/meta의 role 요약만 fact-backed source 기준으로 좁혀집니다.
- 테스트 보강도 실제로 들어갔습니다. [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9405) 의 `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload`는 첫 응답, 첫 session history entry, 자연어 reload 응답에서 `source_roles == ['백과 기반']`와 `'설명형 출처'` 미포함을 explicit assertion으로 잠급니다. 본문의 `사실 카드:` / `교차 확인` 유지와 `출시일` / `2025` 미노출 assertion도 그대로 유지됩니다.
- 수동 fixture replay 결과도 latest `/work` 주장과 일치합니다. 같은 noisy fixture에서 첫 응답, 자연어 reload, 첫 history badge 모두 `source_roles = ['백과 기반']`로 필터링되었고, 이전 `/verify`가 지적했던 noisy-role leakage는 재현되지 않았습니다.
- docs 무변경도 이번 라운드에서는 허용 가능합니다. 현재 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`는 source-role badge의 존재와 trust label 노출을 일반 수준에서만 설명하고 있고, noisy role filtering의 exact contract까지는 아직 약속하지 않으므로, 이번 라운드의 visible refinement가 docs truth를 깨지는 않았습니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 document-first MVP 안의 secondary web investigation quality hardening이며, ranking rewrite, reinvestigation expansion, docs wording widening, approval/reviewed-memory 확장은 섞이지 않았습니다.
- 다만 latest `/work`의 잔여 리스크 문구처럼 `verification_label = 설명형 다중 출처 합의`는 여전히 남습니다. 현재 재현에서도 첫 응답, 자연어 reload, history badge 모두 이 라벨을 유지합니다. 그러나 이는 동일 role의 wiki 2건이 strong slot을 지지하기 때문에 현재 구현 의미상 곧바로 오동작이라고 단정할 수는 없습니다. 즉 이번 handoff가 요구한 noisy `source_roles` leakage fix의 미완료는 아닙니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 124 tests in 2.510s`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-entity-card-source-roles-noisy-role-filter.md`
  - `verify/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock-verification.md`
  - `.pipeline/codex_feedback.md`
  - `core/agent_loop.py`
  - `tests/test_web_app.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 추가 확인
  - `sed -n '5038,5168p' core/agent_loop.py`
  - `sed -n '9400,9525p' tests/test_web_app.py`
  - `rg -n "_build_web_search_origin|fact bullet|source_roles == \\['백과 기반'\\]|설명형 출처|multi_source_agreement_over_noise_natural_reload|history badge" core/agent_loop.py tests/test_web_app.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_web_app.py work/3/31/2026-03-31-entity-card-source-roles-noisy-role-filter.md verify/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock-verification.md .pipeline/codex_feedback.md`
  - 수동 fixture replay (`WebAppService` + `_FakeWebSearchTool` 동일 noisy fixture)
    - 첫 응답 `response_origin`: `source_roles = ['백과 기반']`, `verification_label = 설명형 다중 출처 합의`
    - 자연어 reload `response_origin`: `source_roles = ['백과 기반']`, `verification_label = 설명형 다중 출처 합의`
    - 첫 session history badge 데이터: `source_roles = ['백과 기반']`, `verification_label = 설명형 다중 출처 합의`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: latest `/work` 변경은 `core/agent_loop.py`의 source-role summarization 최소 fix와 `tests/test_web_app.py` regression 보강에 그쳤고, browser-visible markup/CSS, stored schema, docs contract 자체는 바뀌지 않았기 때문입니다.

## 남은 리스크
- 이번 handoff가 요구한 exact slice인 noisy `source_roles` leakage는 truthfully 닫혔습니다. 첫 응답, 자연어 reload, history badge 모두 이제 noisy single-source role을 다시 노출하지 않습니다.
- 다음 단계는 구현 문제가 아니라 의미 결정에 가깝습니다. `source_roles`가 `['백과 기반']`로 좁혀진 뒤에도 `verification_label = 설명형 다중 출처 합의`를 유지할지, 아니면 같은 family에서 label semantics까지 다시 맞출지부터 정해야 합니다.
- 따라서 다음 `.pipeline/codex_feedback.md`는 `STATUS: needs_operator`로 두고, operator가
  - `A`축을 여기서 닫고 새 quality axis를 열지,
  - 아니면 같은 family 안에서 `verification_label` semantics를 다시 다룰지
  를 먼저 정하는 편이 맞습니다.
- dirty worktree가 여전히 넓어서 다음 검수도 scoped verification discipline이 계속 필요합니다.
