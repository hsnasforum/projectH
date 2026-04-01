# 2026-03-31 latest-update noisy source filtering verification

## 변경 파일
- `verify/3/31/2026-03-31-latest-update-noisy-source-filtering-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-latest-update-noisy-source-filtering.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-entity-card-source-roles-noisy-role-filter-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 operator가 새 quality axis `B: latest_update answer-mode noise filtering`을 선택한 뒤 same-family 첫 slice로 latest_update 본문·badge·source_roles에서 noisy community source가 다시 노출되지 않도록 잠갔다고 적고 있으므로, 이번 검수에서는 그 코드 변경이 실제로 들어갔는지, 새 regression이 실제 경로를 덮는지, docs 무변경이 still truthful한지, 그리고 필요한 최소 검증만 재실행하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 코드 변경은 실제로 반영되어 있습니다. [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5051) 의 `_build_web_search_origin`은 `answer_mode == "latest_update"`일 때 noisy `summary_text` / `snippet` source를 `source_roles` 산출 대상에서 제외하고, [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5170) 의 `_build_latest_update_web_summary`도 동일 noisy 필터를 `출처 성격:` 줄 산출에 적용합니다. fallback으로 모든 source가 탈락하면 원래 목록을 유지하는 점도 `/work`와 일치합니다.
- 테스트 보강도 실제로 들어갔습니다. [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9518) 의 `test_handle_chat_latest_update_noisy_source_excluded_from_body_and_badge`는 뉴스 2개 + noisy community 1개 fixture에서 첫 응답, 첫 history badge, 자연어 reload 모두에 대해 `보조 커뮤니티` role과 `brunch` URL이 다시 노출되지 않는지를 explicit assertion으로 잠급니다.
- `/work`의 검증 자기보고도 현재는 truthful합니다. `python3 -m unittest -v tests.test_web_app`를 다시 돌려 `Ran 125 tests in 3.215s`, `OK`를 확인했고, `python3 -m unittest -q tests.test_web_app`도 `Ran 125 tests`, `OK`로 같은 count를 재확인했습니다. `git diff --check -- core/agent_loop.py tests/test_web_app.py`도 통과했습니다.
- docs 무변경도 이번 라운드에서는 허용 가능합니다. 현재 dirty worktree에 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md` 수정이 보이지만, `stat` 기준 이들 파일의 mtime은 모두 이번 `/work`보다 훨씬 이전입니다. 즉 latest Claude round가 이번 noisy latest_update slice와 직접 연결해 새 docs hunk를 만든 흔적은 없고, latest `/work`가 문서 변경을 주장하지 않은 것도 이번 round-local truth와 충돌하지 않습니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 document-first MVP 안의 secondary web investigation hardening이며, ranking rewrite, broader source-policy overhaul, approval/reviewed-memory 확장, browser-visible UI markup 변경은 섞이지 않았습니다.
- 추가 확인: latest `/work`가 남긴 "history-card `load_web_search_record_id` reload 경로는 별도 테스트 없음"도 사실입니다. 현재 테스트 파일에는 latest_update noisy filtering의 자연어 reload regression만 있고, `load_web_search_record_id` 기반 noisy-filter regression은 없습니다. 다만 수동 fixture replay로는 현재 코드가 그 경로에서도 noisy role/URL을 억제함을 확인했습니다.
- 참고: 이번 `/work`는 이전 `needs_operator`를 무시한 라운드가 아닙니다. [` .pipeline/codex_feedback.md`](/home/xpdlqj/code/projectH/.pipeline/codex_feedback.md)의 mtime이 latest `/work`보다 앞서고, 내용도 operator가 `B`축과 `STATUS: implement`를 명시한 상태였습니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 125 tests in 3.215s`, `OK`)
- `python3 -m unittest -q tests.test_web_app`
  - 통과 (`Ran 125 tests in 3.190s`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-latest-update-noisy-source-filtering.md`
  - `verify/3/31/2026-03-31-entity-card-source-roles-noisy-role-filter-verification.md`
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
  - `sed -n '5168,5238p' core/agent_loop.py`
  - `sed -n '9520,9660p' tests/test_web_app.py`
  - `rg -n "latest_update.*noisy|noisy source|보조 커뮤니티|brunch|load_web_search_record_id.*latest_update|latest_update.*history card|history-card.*latest_update" tests/test_web_app.py`
  - `stat -c '%y %n' README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md core/agent_loop.py tests/test_web_app.py work/3/31/2026-03-31-latest-update-noisy-source-filtering.md .pipeline/codex_feedback.md`
  - 수동 fixture replay (`WebAppService` + `_FakeWebSearchTool` 동일 latest_update noisy fixture)
    - 자연어 reload는 `source_roles`에서 `보조 커뮤니티`를 노출하지 않음
    - `load_web_search_record_id` reload도 `response_origin.source_roles = ['보조 출처', '보조 기사']`, 본문 `brunch` 미노출로 동작함
- 이번 라운드에서 재실행하지 않은 검증
  - `python3 -m unittest -v tests.test_smoke`
  - `make e2e-test`
  - 이유: latest `/work` 변경은 `core/agent_loop.py`의 latest_update noisy filtering 최소 fix와 `tests/test_web_app.py` regression 1건 추가에 그쳤고, browser-visible markup/CSS, stored schema, docs contract 자체는 바뀌지 않았기 때문입니다.

## 남은 리스크
- latest_update noisy filtering family의 첫 slice는 truthfully 닫혔습니다. 첫 응답, 첫 history badge, 자연어 reload 모두 noisy community role/URL을 다시 노출하지 않습니다.
- 같은 family의 다음 smallest current-risk는 history-card `load_web_search_record_id` reload 경로의 explicit regression lock입니다. 수동 재현으로는 현재 코드가 이미 noisy role/URL을 억제하지만, 그 shipped path를 잠그는 테스트는 아직 없습니다.
- current worktree에는 unrelated dirty docs 변경이 넓게 섞여 있으므로, 다음 라운드도 scoped verification discipline이 계속 필요합니다.
