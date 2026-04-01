# 2026-03-31 multi-source agreement over noise reload lock verification

## 변경 파일
- `verify/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-multi-source-agreement-reload-retention-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 history-card `load_web_search_record_id` reload 경로에서 `multi-source agreement / single-source noise` slice를 `tests/test_web_app.py` 1건으로 truthfully 닫았다고 적고 있으므로, 이번 검수에서는 noisy-source fixture와 omission assertion이 실제로 들어갔는지, production/docs 무변경 주장이 맞는지, 현재 MVP 방향을 벗어나지 않았는지, 그리고 필요한 최소 검증만 재실행하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 코드 변경은 실제로 반영되어 있습니다. [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9285) 의 `test_handle_chat_entity_card_multi_source_agreement_retained_after_history_card_reload`에는 agreeing wiki 2개에 noisy blog source 1개가 실제로 추가되어 있고, 첫 응답과 `load_web_search_record_id` reload 응답 양쪽 모두에서 `사실 카드:` / `교차 확인` 유지와 `출시일` / `2025` 미노출을 explicit assertion으로 잠그고 있습니다.
- latest `/work`의 test-only 범위 주장도 대체로 맞습니다. 이번 라운드와 직접 대응되는 새 production/docs 변경은 확인되지 않았고, [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5894) 의 reload summary reconstruction 경로는 이전과 같은 위치에 그대로 있습니다. current projectH 방향도 벗어나지 않았습니다. 이번 라운드는 여전히 document-first MVP 안의 secondary web investigation quality hardening이며, ranking rewrite, reinvestigation expansion, approval/UI 확장은 섞이지 않았습니다.
- 다만 `/work` 본문에는 세부 과장이 1건 있습니다. note는 "strong slot 유지, weak/strong 비중첩 assertion 유지"를 적었지만, 현재 이 테스트는 weak item overlap을 직접 assert하지 않습니다. 이는 closeout 문구 정밀도의 문제이지, 이번 slice의 핵심 closure 자체를 뒤집는 수준은 아닙니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 123 tests in 2.611s`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock.md`
  - `verify/3/31/2026-03-31-multi-source-agreement-reload-retention-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 추가 확인
  - `sed -n '9280,9425p' tests/test_web_app.py`
  - `sed -n '5888,6035p' core/agent_loop.py`
  - `rg -n "agreement|single-source|noisy|방금 검색한 결과 다시 보여줘|recent-record|자연어.*reload" tests/test_web_app.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_web_app.py work/3/31/2026-03-31-multi-source-agreement-reload-retention.md verify/3/31/2026-03-31-multi-source-agreement-reload-retention-verification.md work/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock.md .pipeline/codex_feedback.md`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: 이번 변경은 `tests/test_web_app.py` 내부 regression 1건 보강에 그쳤고, browser-visible markup/CSS, approval flow, stored schema, docs contract 자체는 바뀌지 않았기 때문입니다.

## 남은 리스크
- history-card `load_web_search_record_id` 경로의 `agreement over noise` slice는 이제 truthfully 닫혔습니다.
- 같은 family의 다음 smallest current-risk는 자연어 recent-record reload 경로입니다. [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L8601), [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9151) 에 exact-field/weak-missing retention 계열은 있지만, agreeing source 2개 + noisy source 1개 fixture에서 `방금 검색한 결과 다시 보여줘`가 noisy claim omission까지 유지하는 explicit regression은 아직 없습니다.
- 다음 `/work` closeout은 실제 assertion 범위만 적어야 합니다. 현재처럼 test가 하지 않는 weak/strong overlap assertion을 note에 다시 섞으면 round truth sync가 다시 흐려집니다.
- dirty worktree가 여전히 넓어서 다음 검수도 scoped verification discipline이 계속 필요합니다.
