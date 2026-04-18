# 2026-04-17 entity-card reinvestigation top-3 ranking verification

## 변경 파일
- `verify/4/17/2026-04-17-entity-card-reinvestigation-top3-ranking-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 오늘 최신 `/work`인 `work/4/17/2026-04-17-entity-card-reinvestigation-top3-ranking.md`가 permission-gated entity-card web investigation의 follow-up suggestion ranking을 바꾸었다고 기록했으므로, 실제 구현/테스트/검증 섹션이 모두 현재 트리와 맞는지 다시 확인해야 했습니다.
- 같은 날짜의 최신 `/verify`는 아직 `verify/4/17/2026-04-17-docs-pipeline-runtime-adoption-cutover-verification-default-cleanup-verification.md`였고, 이번 entity-card 슬라이스에 대한 matching `/verify`는 없었습니다. 따라서 이번 round는 새 verification note를 남기는 것이 맞습니다.

## 핵심 변경
- 지정된 `/work`는 오늘 최신 closeout과 일치합니다. `ls -1t work/4/17 | head -n 5` 결과에서 `2026-04-17-entity-card-reinvestigation-top3-ranking.md`가 최상단이었고, 같은 날짜 최신 `/verify`는 아직 runtime-docs cleanup note였습니다.
- `/work`가 적은 구현 범위는 현재 트리와 맞습니다. `git diff --stat -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`는 정확히 3개 파일만 보여 주며, `core/agent_loop.py:2489-2559`에는 `_REINVESTIGATION_SLOT_USER_PRIORITY`와 `(status_rank, sub_rank, slot_rank, stored_index)` 정렬이 실제로 들어가 있습니다.
- 새 회귀 테스트도 `/work` 설명과 맞습니다.
  - `tests/test_smoke.py:1947-2048`의 `test_entity_reinvestigation_top3_ranks_by_slot_value_and_source_fragility_over_stored_order`
  - `tests/test_web_app.py:14560-14681`의 `test_handle_chat_load_web_search_record_id_entity_reinvestigation_top3_ranks_by_slot_value_and_source_fragility`
  두 테스트 모두 raw stored order 대신 blank `missing` / fragile `weak` 우선순위를 직접 잠그고, generic fallback prompt 순서까지 확인합니다.
- `/work`의 검증 섹션도 현재 기준으로 truthful합니다. 제가 같은 명령을 다시 돌린 결과:
  - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` 통과
  - `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 3 tests`, `OK`
  - `python3 -m unittest tests.test_web_app -k reinvestigation` → `Ran 3 tests`, `OK`
  - `python3 -m unittest tests.test_smoke -k claim_coverage` → `Ran 5 tests`, `OK`
  - `python3 -m unittest tests.test_web_app -k claim_coverage` → `Ran 21 tests`, `OK`
  - `python3 -m unittest tests.test_smoke -k entity` → `Ran 21 tests`, `OK`
  - `python3 -m unittest tests.test_web_app -k entity` → `Ran 55 tests`, `OK`
  - `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py` 출력 없음
- 이번 변경은 current MVP 경계를 넘지 않습니다. `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`, `docs/MILESTONES.md` 모두 web investigation을 secondary mode로 유지하고 있고, 이번 슬라이스는 그 안의 entity-card quality 개선 한 조각으로 해석하는 것이 맞습니다.
- 다만 다음 exact slice는 아직 저신뢰입니다. 현재 문서와 코드 검색으로는 같은 browser-investigation family 안에서
  - agreement-over-noise의 다음 bounded slice,
  - reinvestigation ranking/fragility의 다음 bounded slice,
  - strong/weak/missing distinction clarity의 다음 bounded slice
  중 하나가 다른 후보를 명확히 이긴다고 보기 어려웠습니다. 그래서 이번 round의 다음 control은 speculative implement handoff보다 Gemini arbitration으로 좁히는 편이 맞습니다.

## 검증
- `ls -1t work/4/17 | head -n 5`
- `ls -1t verify/4/17 | head -n 5`
  - 결과: 지정된 `/work`가 오늘 최신 closeout이고, entity-card 슬라이스의 matching `/verify`는 아직 없었습니다.
- `git status --short`
  - 결과: 현재 트리에는 이번 3개 구현 파일 외에도 runtime-docs 5개, `verify/4/9/...` 2개, Gemini report/work/verify note 등의 unrelated dirty/untracked 항목이 함께 존재했습니다.
- `git diff --stat -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - 결과: 3 files changed, 269 insertions(+), 4 deletions(-)
- `git diff --unified=0 -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `nl -ba core/agent_loop.py | sed -n '2488,2560p'`
- `nl -ba tests/test_smoke.py | sed -n '1945,2048p'`
- `nl -ba tests/test_web_app.py | sed -n '14555,14695p'`
  - 결과: `/work`가 설명한 ranking heuristic과 새 회귀 테스트가 실제 파일에 존재함을 확인했습니다.
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - 결과: 통과
- `python3 -m unittest tests.test_smoke -k reinvestigation`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_web_app -k reinvestigation`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest tests.test_smoke -k claim_coverage`
  - 결과: `Ran 5 tests`, `OK`
- `python3 -m unittest tests.test_web_app -k claim_coverage`
  - 결과: `Ran 21 tests`, `OK`
- `python3 -m unittest tests.test_smoke -k entity`
  - 결과: `Ran 21 tests`, `OK`
- `python3 -m unittest tests.test_web_app -k entity`
  - 결과: `Ran 55 tests`, `OK`
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - 결과: 출력 없음
- Playwright / `make e2e-test`
  - 미실행. 이번 변경은 suggestion ranking과 Python regression 범위였고, 브라우저 helper/layout/copy/selector를 건드리지 않았으므로 focused Python rerun이 가장 좁은 관련 검증이었습니다.

## 남은 리스크
- `_REINVESTIGATION_SLOT_USER_PRIORITY`는 현재 `CORE_ENTITY_SLOTS` 5개에 대한 고정 map이라, 다른 도메인/entity family로 확장될 때는 재조정 또는 shared helper 승격이 필요할 수 있습니다.
- WEAK 슬롯에서 `source_role`이 비어 있으면 untrusted로 취급됩니다. legacy stored record 중 실제로는 trusted source였지만 role이 비어 있는 케이스가 있다면 top-3 순서가 보수적으로 바뀔 수 있습니다.
- 이번 round로 latest `/work`의 구현/검증 주장은 truthful하게 닫혔지만, 바로 다음 exact slice는 아직 저신뢰입니다. 새 Claude implement handoff를 억지로 쓰기보다 Gemini에게 현재 browser-investigation family의 다음 bounded slice를 다시 좁히게 하는 편이 맞습니다.
