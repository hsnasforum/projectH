# 2026-04-19 reinvestigation conflict suggestions probe cap verification

## 변경 파일
- `verify/4/19/2026-04-19-reinvestigation-conflict-suggestions-probe-cap-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-reinvestigation-conflict-suggestions-probe-cap.md`)의 code 주장을 현재 tree와 대조하고, 같은 날 선행 verify(`source-role-news-priority-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 400 (`Milestone 4 Reinvestigation — CONFLICT slot inclusion in suggestions + probe retry cap`)는 Gemini advice 399가 지정한 두 가지 정확한 변경(`_build_entity_reinvestigation_suggestions::status_priority`에 `CoverageStatus.CONFLICT: 2` 추가, 그리고 second-pass `max_queries_for_slot`의 WEAK 비교를 `{WEAK, CONFLICT}`로 확장)만 적용하는 code-only 슬라이스였습니다.
- 이번 `/work`가 `core/agent_loop.py` 두 지점과 `tests/test_smoke.py` 두 개의 새 coverage 회귀, 그리고 seq 369 probe guard / seq 385 focus-slot wording / 모든 seq 388/391/394/397 source-role priority entries가 untouched 상태임을 주장했으므로, 각 변경이 현재 tree와 일치하는지와 scope_limit을 넘지 않았는지 이번 verify에서 고정해야 합니다.
- 선행 verify(`source-role-news-priority-verification`)는 seq 397 NEWS elevation round 전용이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/agent_loop.py:2519-2522` `status_priority`가 이제 `{CoverageStatus.MISSING: 0, CoverageStatus.WEAK: 1, CoverageStatus.CONFLICT: 2}`입니다. `status not in status_priority` gate(기존 line), `status_rank` lookup, candidate tuple shape, `slot_prompt_map`은 수정되지 않았습니다.
  - `core/agent_loop.py::max_queries_for_slot`의 WEAK 비교가 `slot_coverage.status in {CoverageStatus.WEAK, CoverageStatus.CONFLICT}`로 확장됐습니다. `prior_probe_count >= 1 or source_role != SourceRole.OFFICIAL` boost 조건은 동일 유지. `prefer_probe_first`, `ordered_variants`, `seen_queries`, `len(second_pass_queries) >= 4` cap은 수정되지 않았습니다.
  - `tests/test_smoke.py:2053` `test_coverage_reinvestigation_suggestions_include_conflict_slot_when_only_conflict_is_pending`과 `:2071` `test_coverage_reinvestigation_second_pass_conflict_slot_uses_weak_like_probe_boost_rules`가 추가됐습니다. 두 테스트 모두 `coverage` 필터에 걸리도록 이름이 지어져 있고, 첫 번째는 CONFLICT-only fixture에서 suggestion 출력을, 두 번째는 non-OFFICIAL CONFLICT slot이 2-query를 받고 OFFICIAL + `prior_probe_count == 0`이면 1-query로 남는지 고정합니다.
- `/work`가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `_claim_coverage_status_rank`, `_claim_coverage_status_label`, `_build_claim_coverage_progress_summary`(seq 385 focus-slot CONFLICT 템플릿 포함), `_build_entity_slot_probe_queries` probe guard(seq 369), `core/contracts.py`, `core/web_claims.py` conflict emission, `storage/web_search_store.py`, `app/serializers.py`, `app/static/contracts.js`, `app/static/app.js`, `app/static/style.css`, `e2e/tests/web-smoke.spec.mjs`, `tests/test_web_app.py`, 그리고 모든 `docs/*.md`는 이번 라운드에서 수정되지 않았습니다.
  - `_ROLE_PRIORITY` entries(seq 388/391/394/397)는 그대로 유지됩니다.
- focused rerun이 모두 통과했습니다.
  - `python3 -m unittest tests.test_smoke -k coverage` → 이번 verify 독립 실행, `Ran 16 tests in 0.055s`, `OK`. seq 397 verify의 14건에서 새 reinvestigation coverage 회귀 2건이 추가돼 16건이 됐습니다.
  - `python3 -m unittest tests.test_smoke -k claims` → 이번 verify 독립 실행, `Ran 5 tests in 0.000s`, `OK`. seq 397 verify의 5건과 동일합니다.
  - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` → `/work`가 이미 실행, 출력 없음, exit `0`.
  - `git diff --check -- core/agent_loop.py tests/test_smoke.py` → 이번 verify 독립 실행, 출력 없음, exit `0`.
- docs-sync drift는 `/work`가 기록한 것보다 실제로는 더 넓습니다.
  - `/work`는 `docs/PRODUCT_SPEC.md:369` "weak/missing slots targeted first in reinvestigation suggestions" 문장만 후속 후보로 기록했지만, 이번 verify에서 `rg -n "\[교차 확인\].{0,60}\[단일 출처\].{0,60}\[미확인\]|reinforced.{0,20}regressed.{0,20}still single-source.{0,20}still unresolved" docs`로 더 대조한 결과, 같은 family의 이전 라운드(seq 382 panel-hint 4-tag, seq 385 focus-slot CONFLICT wording, 이번 seq 400 reinvestigation CONFLICT)에 뒤따라 syncing이 필요한 다른 stale 문장이 `docs/PRODUCT_SPEC.md` 안에만도 여러 개 존재합니다.
    - `docs/PRODUCT_SPEC.md:107` "claim coverage panel with status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`), ... dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved)" — panel 3-tag와 focus-slot 4-state 모두 이제 시대 지남.
    - `docs/PRODUCT_SPEC.md:155` "claim coverage panel ... dedicated plain-language focus-slot reinvestigation explanation covering reinforced / regressed / still single-source / still unresolved" — focus-slot 4-state stale.
    - `docs/PRODUCT_SPEC.md:344` "status tags (`[교차 확인]`, `[단일 출처]`, `[미확인]`) leading each slot line" — panel 3-tag stale.
    - `docs/PRODUCT_SPEC.md:348` "telling the user whether the slot was reinforced, regressed, is still single-source, or is still unresolved" — focus-slot 4-state stale.
    - `docs/PRODUCT_SPEC.md:367` panel 3-tag + focus-slot 4-state 모두 stale.
    - `docs/PRODUCT_SPEC.md:369` `/work`가 이미 flag한 reinvestigation suggestion 문장.
    - `docs/PRODUCT_SPEC.md:370` response-body 3-tag는 `docs/ACCEPTANCE_CRITERIA.md:49` 주장(response-body emit는 여전히 3-tag)과 일치하므로 문자 자체는 truthful. "matching claim-coverage panel statuses" 구절만 panel이 4-tag가 되면서 일부 모호하나, 엄밀한 오류는 아님.
  - 추가로 `docs/ARCHITECTURE.md:11/142/1377`, `docs/PRODUCT_PROPOSAL.md:26/65`, `docs/project-brief.md:15/89`, `docs/TASK_BACKLOG.md:25`(bar는 seq 381에서 synced됐지만 focus-slot 4-state 꼬리가 stale)에도 동일 패턴의 drift가 남아 있습니다. 다만 이 파일들은 current-contract vs roadmap framing 성격이 섞여 있어, 다음 슬라이스는 `docs/PRODUCT_SPEC.md` 한 파일 안의 current-contract sentences에 먼저 좁혀 bounded 묶음으로 닫는 편이 truthful하고, 나머지 4개 파일은 다음-다음 라운드의 별도 bounded bundle 후보로 남깁니다.
- 같은 날 same-family docs-only round count는 seq 381의 1회 그대로입니다. `docs/PRODUCT_SPEC.md`만 targeted한 다음 슬라이스는 docs-only round 2가 되며, `3+ docs-only` guard는 아직 트리거되지 않습니다. 추가 docs 라운드가 3번째로 내려가지 않도록 다음 슬라이스는 `docs/PRODUCT_SPEC.md` 안의 CONFLICT-family stale 문장을 한 번에 닫는 bounded 묶음으로 가는 편이 쌓인 drift를 가장 적은 round 수로 해소합니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `core/agent_loop.py:2519-2522` / `:3843-3846`, `tests/test_smoke.py:2053` / `:2071`, 그리고 `docs/PRODUCT_SPEC.md:107/155/344/347/348/367/369/370`.
  - 결과: `/work`가 설명한 code 변경이 현재 tree와 일치하고, CONFLICT-family 관련 shipped surface(label/rank/unresolved/probe/focus-slot wording/source-role weighting/browser/Playwright)가 실제로 untouched입니다. docs drift 범위는 `/work`가 언급한 line 369 외에 line 107/155/344/348/367에도 확장되어 있음을 확인했습니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 16 tests in 0.055s`, `OK`.
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.000s`, `OK`.
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - Playwright 스위트: 이번 라운드는 Python reinvestigation 두 지점과 focused smoke regression만 건드렸고 browser-visible copy/shared helper/fixture는 바뀌지 않았습니다. `.claude/rules/browser-e2e.md`의 "isolated Playwright rerun 우선" 기준 아래에서 생략이 truthful합니다.
  - 전체 `python3 -m unittest tests.test_web_app`: 이번 라운드는 `tests.test_web_app` 경로를 전혀 건드리지 않았고, 기존 실패 family(37 errors)는 선행 verify들에서 별도 dirty-state truth-sync 라운드 몫으로 분리돼 있습니다.
  - `make e2e-test`: release/ready 판정 라운드가 아니고 shared helper 변경도 없으므로 생략합니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md` 안의 CONFLICT-family stale 문장(`:107`, `:155`, `:344`, `:348`, `:367`, `:369`)은 이번 라운드에서 바로 닫아야 할 같은 family current-risk입니다. 다음 슬라이스는 이 한 파일만 대상으로 하는 bounded docs-sync 묶음으로 제안합니다.
- `docs/ARCHITECTURE.md:11/142/1377`, `docs/PRODUCT_PROPOSAL.md:26/65`, `docs/project-brief.md:15/89`, `docs/TASK_BACKLOG.md:25` tail에도 같은 패턴(focus-slot 4-state 혹은 panel 3-tag)의 잔여 drift가 있습니다. 이 4개 파일은 다음-다음 라운드의 별도 bounded bundle로 남깁니다. 다음 라운드와 합치면 docs-only round 2회 연속이 되지만 그 후 code 라운드로 돌아가면 `3+ docs-only same-family` guard까지 여유가 남습니다.
- Milestone 4 다른 sub-axis(COMMUNITY/PORTAL/BLOG weighting, strong-vs-weak-vs-unresolved separation beyond CONFLICT, response-body `[정보 상충]` tag emission, reinvestigation threshold/probe retry 추가 tuning)는 여전히 별도 future slice 후보입니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family와 `tests.test_pipeline_gui_backend::TestRuntimeStatusRead`는 이번 슬라이스와 무관하며 여전히 dirty-state 기반 별도 truth-sync 라운드 몫입니다.
