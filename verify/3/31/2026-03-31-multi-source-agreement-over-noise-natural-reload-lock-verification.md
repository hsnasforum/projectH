# 2026-03-31 multi-source agreement over noise natural reload lock verification

## 변경 파일
- `verify/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 same-family follow-up으로 자연어 recent-record reload 경로의 `agreement over noise` 텍스트 유지 여부를 `tests/test_web_app.py` 1건으로 잠갔다고 적고 있으므로, 이번 검수에서는 새 테스트 존재 여부, noisy-source fixture/assertion의 실제 반영 여부, production/docs 무변경 주장, 현재 MVP 방향 일탈 여부, 그리고 필요한 최소 검증만 재실행하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 코드 변경은 실제로 반영되어 있습니다. [`tests/test_web_app.py#L9405`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9405) 의 `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload`가 실제로 추가되었고, fixture에는 agreeing wiki 2개와 noisy blog source 1개가 들어 있으며, 첫 응답과 자연어 reload (`"방금 검색한 결과 다시 보여줘"`) 양쪽 모두에서 `사실 카드:` / `교차 확인` 유지와 `출시일` / `2025` 미노출을 explicit assertion으로 잠그고 있습니다.
- latest `/work`의 test-only 범위 주장도 맞습니다. 이번 라운드와 직접 대응되는 새 production/docs 변경은 확인되지 않았고, [`core/agent_loop.py#L5894`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5894) 의 reload summary reconstruction 경로는 이전과 같은 위치에 그대로 있습니다. 현재 방향도 document-first MVP 안의 secondary web investigation hardening에 머물러 있으며, ranking rewrite, reinvestigation expansion, approval/UI 확장은 섞이지 않았습니다.
- 다만 `/work`의 마지막 문장인 "이 family는 닫힘"은 아직 과합니다. 수동 fixture replay 결과, 같은 noisy-source fixture에서도 첫 응답과 자연어 reload의 `response_origin.source_roles`가 둘 다 `['백과 기반', '설명형 출처']`로 남고, session history header용 stored badges도 같은 값을 저장합니다. 즉 noisy single-source claim은 본문에서 억제되지만, noisy source role은 여전히 user-visible badge/meta에 노출됩니다. 이 점 때문에 same family의 user-visible slice 1개가 남아 있습니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 124 tests in 2.402s`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock.md`
  - `verify/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock-verification.md`
  - `.pipeline/codex_feedback.md`
  - `tests/test_web_app.py`
  - `core/agent_loop.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/NEXT_STEPS.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
- 추가 확인
  - `sed -n '9388,9505p' tests/test_web_app.py`
  - `sed -n '5888,6035p' core/agent_loop.py`
  - `rg -n "multi_source_agreement|agreement_over_noise|noisy|방금 검색한 결과 다시 보여줘|natural reload|자연어 reload|agreement-backed" tests/test_web_app.py`
  - `stat -c '%y %n' core/agent_loop.py tests/test_web_app.py work/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock.md verify/3/31/2026-03-31-multi-source-agreement-over-noise-reload-lock-verification.md work/3/31/2026-03-31-multi-source-agreement-over-noise-natural-reload-lock.md .pipeline/codex_feedback.md`
  - 수동 fixture replay (`WebAppService` + `_FakeWebSearchTool` 동일 noisy fixture)
    - 첫 응답 `response_origin`: `verification_label = 설명형 다중 출처 합의`, `source_roles = ['백과 기반', '설명형 출처']`
    - 자연어 reload `response_origin`: `verification_label = 설명형 다중 출처 합의`, `source_roles = ['백과 기반', '설명형 출처']`
    - 첫 session history badge 데이터: `answer_mode = entity_card`, `verification_label = 설명형 다중 출처 합의`, `source_roles = ['백과 기반', '설명형 출처']`
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: latest `/work` 변경은 `tests/test_web_app.py` regression 1건 추가뿐이었고, browser-visible markup/CSS, approval flow, stored schema, docs contract 자체는 바뀌지 않았기 때문입니다.

## 남은 리스크
- summary text 기준으로는 `multi-source agreement / single-source noise`가 history-card reload + 자연어 reload 두 경로 모두 잠겼습니다.
- 그러나 same family의 user-visible badge/meta는 아직 완전히 닫히지 않았습니다. noisy single-source의 role이 initial response, natural reload response, history-card header 저장값에 계속 노출되어 `agreement over noise`를 badge 층에서 흐립니다.
- 따라서 다음 Claude handoff는 새 축으로 넘어가기보다, 같은 family 안에서 `response_origin` / history-card `source_roles`에서 noisy single-source role을 억제하는 user-visible slice 1개로 유지하는 편이 맞습니다.
- dirty worktree가 여전히 넓어서 다음 검수도 scoped verification discipline이 계속 필요합니다.
