# 2026-04-20 source role weighting portal community verification

## 변경 파일
- `verify/4/20/2026-04-20-source-role-weighting-portal-community-verification.md`

## 사용 skill
- `round-handoff`: seq 420 `/work`(`work/4/20/2026-04-20-source-role-weighting-portal-community.md`) 주장 내용을 `core/web_claims.py`, `core/agent_loop.py` mirror 2곳, `tests/test_smoke.py` 실제 상태와 직접 대조한 뒤 narrowest 검증을 재실행해 truthful 여부를 확정했습니다.

## 변경 이유
- seq 420 `.pipeline/claude_handoff.md`(Gemini 419 Option C 기반)가 구현되어 새 `/work` 노트가 제출되었습니다. 목표는 Milestone 4 source role weighting에서 shared 0-tier 를 쪼개 `COMMUNITY`/`PORTAL`을 1로 올리고 `BLOG`를 strict bottom(0)에 남기면서 세 `_ROLE_PRIORITY` 맵(`core/web_claims.py` master + `core/agent_loop.py` 2곳 mirror)을 동시에 동일하게 유지하는 것이었고, 본 verify는 그 주장을 실제 파일과 테스트로 교차 확인합니다.

## 핵심 변경
- `core/web_claims.py:32-42` `_ROLE_PRIORITY`는 이제 `OFFICIAL:5 / WIKI:4 / DATABASE:4 / DESCRIPTIVE:3 / NEWS:2 / AUXILIARY:1 / COMMUNITY:1 / PORTAL:1 / BLOG:0` 이며, 키 순서는 변경되지 않았습니다. 이전 `COMMUNITY:0 / PORTAL:0`만 1로 이동, 나머지 포지션은 그대로 유지되었습니다.
- `core/agent_loop.py:4131-4141` `_entity_claim_sort_key` mirror 와 `core/agent_loop.py:4545-4555` `_build_entity_claim_source_lines` mirror 두 맵 모두 `COMMUNITY:1 / PORTAL:1 / BLOG:0` 으로 이동해 master와 정확히 동일합니다. 나머지 OFFICIAL/WIKI/DATABASE/DESCRIPTIVE/NEWS/AUXILIARY 포지션은 master와 일치하며 키 순서도 그대로입니다. seq 411 sync invariant가 깨지지 않았습니다.
- `tests/test_smoke.py:2647-2683` 에 `test_claims_source_role_priority_splits_portal_community_above_blog` 가 추가되었습니다. 위치는 `test_claims_source_role_priority_places_news_above_auxiliary_below_descriptive`(`:2613-2645`) 직후, `test_claim_coverage_conflict_status_label_rank_and_probe_queries`(`:2685-`) 직전으로 handoff 지시와 일치합니다.
- 새 회귀 내용:
  - `_ROLE_PRIORITY[SourceRole.COMMUNITY] == 1`, `PORTAL == 1`, `BLOG == 0`, `AUXILIARY == 1` 을 값 기준으로 직접 고정.
  - `COMMUNITY > BLOG`, `PORTAL > BLOG`, `NEWS > COMMUNITY` 관계 assertion 포함.
  - `summarize_slot_coverage([blog_claim, portal_claim], slots=("이용 형태",))` 호출로 support_count tie(1 vs 1)일 때 primary claim 이 `PORTAL` 쪽으로 선택됨을 behavior 기준으로 확인합니다.
- handoff 가 금지한 surface 는 그대로 유지되었습니다: `_role_confidence_score`(float axis, `core/agent_loop.py:4108-4110`), seq 385/400/405/408/411/414/417 CONFLICT chain surface, docs, Playwright scenario, `app/*`, `storage/*`, agent-config 파일은 이번 라운드에서 수정되지 않았습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 6 tests in 0.001s`, `OK`. 기존 5 + 신규 1. 기존 `NEWS > COMMUNITY` assertion(`:2641`)은 2 > 1 로 여전히 참이라 회귀 없음.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 19 tests in 0.058s`, `OK`. coverage 회귀는 COMMUNITY/PORTAL tier change 와 독립적인 OFFICIAL/WIKI/DATABASE/NEWS fixture 를 쓰므로 영향 없음.
- `python3 -m py_compile core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- core/web_claims.py core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과.
- Playwright, `python3 -m unittest tests.test_web_app`, `make e2e-test` 는 실행하지 않았습니다. integer role-priority 와 smoke regression 1건만 바뀌었고 browser copy/selector/shared helper/payload shape 는 무변경이라 `.claude/rules/browser-e2e.md` 기준 broad 검증이 과합니다.

## 남은 리스크
- Milestone 4 남은 후보:
  - D) Reinvestigation threshold / probe retry — `max_queries_for_slot` 상한, probe list 크기, `prefer_probe_first` 문턱 등 단일 상수 한 번의 numeric 조정. `core/agent_loop.py` 내부 해당 상수 `:line` 을 pin 해야 합니다.
  - E) Strong vs Weak vs Unresolved Separation further polish — STRONG-tied-with-STRONG tie-break, entity-card strong-badge downgrade edge, 비-CONFLICT 전이 wording polish 중 한 surface.
- `_role_confidence_score` float axis(`PORTAL:0.45 / BLOG:0.35 / AUXILIARY:0.4`)는 `_ROLE_PRIORITY` integer axis 와 별개로 남아 있으며 별도 tuning round 후보입니다. 이번 라운드는 건드리지 않았습니다.
- step 5 grep 에서 `COMMUNITY`/`PORTAL`/`BLOG` numeric role-priority 를 직접 열거한 docs 문장은 발견되지 않았습니다. 따라서 narrow docs-sync follow-up 은 열 필요가 없었고, 오늘(2026-04-20) docs-only round count 는 계속 0 입니다. 이후 라운드에서 code-only / code+docs mixed / pure docs-only 어느 shape 도 guard 여유가 있습니다.
- unrelated 전체 `python3 -m unittest tests.test_web_app` 실패 family, `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` dirty-state 실패는 이번 slice 밖이며 별도 truth-sync 라운드 몫입니다.
- 다음 control 은 D/E 후보 모두 정확한 file + surface + numeric/textual 경계가 단독으로 pinned 되지 않아 slice_ambiguity 성격이므로, operator-only decision/approval blocker/안전 정지/Gemini 부재 조건에 해당하지 않는 한 `.pipeline/gemini_request.md`(seq 421)로 arbitration 을 먼저 여는 편이 rule 에 맞습니다.
