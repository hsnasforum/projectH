# 2026-03-31 entity-card trust-weighted agreement verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-trust-weighted-agreement-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-trust-weighted-agreement.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-entity-card-source-type-diversity-no-new-work-verification.md`를 기준으로 이번 라운드 production/test 변경 truth를 다시 대조할 필요가 있었습니다.
- 이번 라운드는 직전과 달리 local canonical handoff에 operator 승인 기록이 실제로 남아 있어, 새 trust-weighted agreement 구현이 그 승인 범위와 맞는지부터 확인해야 했습니다.

## 핵심 변경
- latest `/work`가 주장한 trust-weighted agreement 구현은 실제 코드에 있습니다. `_entity_source_fact_agreement_score`는 `trust_score_by_index`를 받고 best peer trust가 높을 때 추가 가중치를 주며, `_select_ranked_web_sources`는 trust score dict를 미리 계산해 agreement 함수에 전달합니다. 근거: [core/agent_loop.py#L3575](/home/xpdlqj/code/projectH/core/agent_loop.py#L3575), [core/agent_loop.py#L4695](/home/xpdlqj/code/projectH/core/agent_loop.py#L4695).
- 새 regression도 실제로 존재합니다. wiki + official + community fixture에서 trust-weighted agreement로 wiki와 official이 선택되고 community가 탈락하는 테스트가 [tests/test_smoke.py#L1535](/home/xpdlqj/code/projectH/tests/test_smoke.py#L1535)에 있습니다.
- 이번 round의 operator 승인 근거는 local canonical 기록으로 확인됩니다. [\.pipeline/codex_feedback.md#L1](/home/xpdlqj/code/projectH/.pipeline/codex_feedback.md#L1)에는 `STATUS: implement`와 함께 option A 선택 및 직전 source-type diversity/live-threshold 승인 기록이 남아 있습니다. 이전 round에서 남았던 operator-flow blocker는 이번 round 기준으로 해소됐습니다.
- 범위도 현재 projectH 방향에서 벗어나지 않습니다. entity-card source ranking 품질 개선은 secondary-mode web investigation의 current-risk reduction 범위 안에 있으며, UI/approval/reviewed-memory 확장은 없었습니다.
- docs 변경이 없다는 latest `/work` 주장도 이번 round에서는 맞습니다. shipped docs는 high-level로 "agreement-backed facts 우선"만 약속하고 있고, exact peer-trust weighting heuristic까지 current contract로 고정하지는 않습니다.
- whole-project audit이 필요한 징후는 아니어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke` : 89 tests, OK
- `python3 -m unittest -v tests.test_web_app` : 106 tests, OK
- `git diff --check -- core/agent_loop.py tests/test_smoke.py` : 통과
- `git diff -- core/agent_loop.py tests/test_smoke.py` : latest `/work` 주장 범위와 실제 diff 대조
- `rg -n "agreement|합의|trust-weighted|source_type|peer trust|백과 기반|공식 기반" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` : current shipped docs가 exact heuristic까지 약속하지 않는 점 확인
- `rg -n "옵션 A|operator가|명시적으로 승인|STATUS: needs_operator|operator 확인 필요" .pipeline work verify` : local canonical operator 승인 기록 확인

## 남은 리스크
- `core/agent_loop.py`에는 이전 round의 source-type diversity cap과 live threshold 완화도 함께 dirty 상태로 남아 있으므로, 다음 검수도 계속 현재 file truth 기준으로 좁게 읽어야 합니다.
- 다음 slice를 current MVP 우선순위 안에서 truthfully 하나로 확정할 근거는 아직 부족합니다. 이 상태에서 또 다른 internal ranking tweak를 자동으로 고르는 것은 과합니다.
- dirty worktree가 여전히 넓음.
