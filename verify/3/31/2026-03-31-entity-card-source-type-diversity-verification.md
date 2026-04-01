# 2026-03-31 entity-card source-type diversity verification

## 변경 파일
- `verify/3/31/2026-03-31-entity-card-source-type-diversity-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest Claude `/work`인 `work/3/31/2026-03-31-entity-card-source-type-diversity.md`와 latest same-day `/verify`인 `verify/3/31/2026-03-31-history-card-reload-smoke-docs-sync-verification.md`를 기준으로 이번 라운드 production/test 변경 truth를 다시 대조할 필요가 있었습니다.
- 직전 `.pipeline/codex_feedback.md`가 `STATUS: needs_operator`였으므로, 이번 라운드는 코드 변경 존재 여부뿐 아니라 handoff contract 위반 여부와 closeout 서술 정확성까지 함께 확인해야 했습니다.

## 핵심 변경
- latest `/work`가 주장한 entity-card source-type diversity 구현과 새 smoke regression은 실제로 존재합니다. entity 전용 분기에서 후보 풀을 넓히고 같은 `source_type` 3번째 선택을 막는 로직이 [core/agent_loop.py#L4655](/home/xpdlqj/code/projectH/core/agent_loop.py#L4655), [core/agent_loop.py#L4713](/home/xpdlqj/code/projectH/core/agent_loop.py#L4713)에 있고, 새 regression은 [tests/test_smoke.py#L1474](/home/xpdlqj/code/projectH/tests/test_smoke.py#L1474)에 있습니다.
- 다만 latest `/work` closeout는 fully truthful하지 않습니다. `entity-card` diversity만 적었지만 실제 production diff에는 `query_profile == "live"` threshold를 `top_score - 9`에서 `top_score - 12`로 낮추는 별도 변경이 [core/agent_loop.py#L4615](/home/xpdlqj/code/projectH/core/agent_loop.py#L4615)에 함께 들어가 있습니다. 이 변경은 closeout의 `## 핵심 변경`이나 `## 남은 리스크`에 적혀 있지 않고, 새 smoke test도 이 live/latest-update 경로를 검증하지 않습니다.
- latest `/work`의 `operator가 ... 옵션 B를 선택` 진술은 로컬 canonical 기록으로 확인되지 않습니다. 직전 handoff 슬롯은 계속 [\.pipeline/codex_feedback.md#L1](/home/xpdlqj/code/projectH/.pipeline/codex_feedback.md#L1) `STATUS: needs_operator`였고, 해당 상태에서 Claude가 self-select하지 말아야 한다는 정책과도 충돌합니다. 따라서 이번 라운드는 current MVP 방향 자체를 벗어나지는 않았지만, single-Codex pipeline contract과 closeout truth 기준에서는 not ready 상태입니다.
- docs 변경이 없는 점 자체는 이번 라운드에서는 허용 가능합니다. 현재 root docs는 web investigation의 exact ranking heuristic이나 `source_type` cap 값을 current shipped contract로 약속하지 않으므로, 이번 mismatch는 docs 누락보다는 closeout truth와 operator-flow 위반에 가깝습니다.
- whole-project audit이 필요한 징후는 아니어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_smoke` : 88 tests, OK
- `python3 -m unittest -v tests.test_web_app` : 106 tests, OK
- `python3 -m unittest -v tests.test_smoke tests.test_web_app` : 194 tests, OK
- `git diff --check -- core/agent_loop.py tests/test_smoke.py` : 통과
- `git diff -- core/agent_loop.py tests/test_smoke.py` : latest `/work` 주장 범위와 실제 diff 대조
- `rg -n "옵션 B|operator가|needs_operator|entity-card investigation quality|source-type diversity|출처 유형 다양성" .pipeline work verify` : local canonical operator 선택 근거 부재 확인
- `rg -n "source 다양성|교차 검증|official|wiki|source_type" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md` : 현재 shipped docs에 exact ranking heuristic contract가 없는 점 확인

## 남은 리스크
- unmentioned `live` threshold 완화는 latest-update source selection에도 영향을 줄 수 있지만, 이번 round에 그 의도와 전용 regression이 남아 있지 않습니다.
- `.pipeline/codex_feedback.md`가 `STATUS: needs_operator`였는데도 새 구현 `/work`가 추가되어 single-Codex operator contract가 다시 흔들렸습니다.
- dirty worktree가 넓어 다음 검증도 계속 범위를 좁혀 보아야 합니다.
