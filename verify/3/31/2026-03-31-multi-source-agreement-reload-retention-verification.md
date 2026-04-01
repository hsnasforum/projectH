# 2026-03-31 multi-source agreement reload retention verification

## 변경 파일
- `verify/3/31/2026-03-31-multi-source-agreement-reload-retention-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-multi-source-agreement-reload-retention.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-entity-card-weak-missing-slot-natural-reload-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 `multi-source agreement / single-source noise` 축에서 entity-card summary text가 `load_web_search_record_id` reload 뒤에도 agreement-backed fact를 유지하고 noisy single-source claim을 다시 노출하지 않는지 `tests/test_web_app.py` 1건으로 잠갔다고 적고 있으므로, 이번 검수에서는 그 test 존재 여부, 실제 fixture/assertion이 handoff 범위를 truthfully 덮는지, production/docs 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 필요한 최소 검증만 다시 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 "test-only slice"와 "production/docs 변경 없음" 주장은 현재 파일 상태와 대체로 일치합니다. `tests/test_web_app.py`에는 `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload`가 실제로 추가되어 있고, `core/agent_loop.py`나 root docs에 이번 라운드와 직접 대응되는 새 hunk는 확인되지 않았습니다.
- 다만 latest `/work`의 핵심 슬라이스 설명은 아직 fully truthful하지 않습니다. 새 테스트 fixture에는 agreeing wiki 2개만 있고, handoff가 요구한 noisy single-source source가 실제로 포함되어 있지 않습니다. 따라서 이 테스트는 "agreement-backed 사실 카드가 reload 후에도 유지되는지"는 보지만, "single-source noisy claim이 다시 노출되지 않는지"는 직접 검증하지 못합니다.
- assertion 범위도 work note를 완전히 따라가지 못합니다. 현재 test는 strong slot 유지, `사실 카드:` 유지, weak slot이 strong slot과 겹치지 않음을 확인하지만, noisy claim omission은 initial/reload 어느 쪽에서도 직접 assert하지 않습니다. 또한 work note가 적은 `weak/missing slot이 strong slot과 겹치지 않음` 중 `missing` 쪽은 현재 assertion으로 직접 확인되지 않습니다.
- 따라서 latest `/work`는 current projectH 방향을 벗어나지는 않았지만, `.pipeline/codex_feedback.md`가 지시한 exact slice를 truthfully 닫았다고 보기는 어렵습니다. 이 라운드는 Milestone 4 secondary-mode investigation hardening 안의 same-family current-risk reduction 시도였고, web investigation remains secondary, read-only, permission-gated, and logged라는 경계 자체는 유지되었습니다.
- whole-project audit이 필요한 징후는 아니므로 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 123 tests`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-multi-source-agreement-reload-retention.md`
  - `verify/3/31/2026-03-31-entity-card-weak-missing-slot-natural-reload-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 추가 확인
  - `sed -n '9278,9408p' tests/test_web_app.py`
  - `sed -n '5888,6035p' core/agent_loop.py`
  - `stat -c '%y %n' tests/test_web_app.py core/agent_loop.py work/3/31/2026-03-31-multi-source-agreement-reload-retention.md .pipeline/codex_feedback.md`
  - `git diff --unified=20 -- tests/test_web_app.py`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests/test_web_app.py` regression 1건만 추가한 test-only slice였고, browser-visible markup/CSS나 docs wording 자체는 바뀌지 않았으므로 `tests.test_web_app`과 scoped diff check만으로 직접 영향 범위를 재검수할 수 있었습니다.

## 남은 리스크
- `multi-source agreement / single-source noise` history-card reload slice는 아직 truthfully 닫히지 않았습니다. current test는 agreement retention은 보지만 noisy single-source suppression을 직접 잠그지 못합니다.
- 따라서 다음 Claude handoff는 operator를 다시 부르지 말고, 같은 history-card `load_web_search_record_id` path에서 fixture에 noisy single-source source 1개를 실제로 추가하고 initial/reload 모두에서 noisy claim omission을 explicit assertion으로 잠그는 same-family current-risk reduction으로 유지하는 편이 맞습니다.
- dirty worktree가 여전히 넓어 다음 검수도 unrelated 변경을 끌어오지 않도록 scoped verification discipline이 계속 필요합니다.
