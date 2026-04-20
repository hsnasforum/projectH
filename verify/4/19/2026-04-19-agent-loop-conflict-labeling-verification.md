# 2026-04-19 agent loop conflict labeling verification

## 변경 파일
- `verify/4/19/2026-04-19-agent-loop-conflict-labeling-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-agent-loop-conflict-labeling.md`)를 현재 tree와 대조해 truth를 재확인하고, 같은 날 직전 verify(`investigation-claim-conflict-status-separation-verification`)를 덮지 않도록 이번 라운드 전용 새 verification 노트를 추가했습니다.

## 변경 이유
- `.pipeline/claude_handoff.md` seq 369가 Gemini advice 368 기반으로 `Agent Loop Coverage Status CONFLICT Labeling` slice를 implement로 닫았고, Codex가 `/work`로 closeout했지만 같은 날 verify 폴더에는 이 family용 verify 노트가 아직 없었습니다.
- 직전 같은 날 verify는 `core/web_claims.py`/`core/contracts.py` 라운드(seq 366)이라 in-place 갱신은 truth loss를 일으킵니다. 따라서 이번 라운드 전용 새 verify 파일을 추가했습니다.
- handoff가 4개 분기(label/rank/unresolved/probe)와 1개 focused regression bundle을 명시했으므로, 4개 모두 truthful하게 들어왔는지와 기존 STRONG/WEAK/MISSING 표면이 회귀하지 않았는지 고정해야 다음 control 선택이 안전합니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `core/agent_loop.py:4317-4325` `_claim_coverage_status_rank`가 `STRONG=3`, `CONFLICT=2`, `WEAK=1`, fall-through `0`을 반환합니다. 같은 슬롯 `WEAK -> CONFLICT` 전이는 더 이상 regression rank로 잡히지 않습니다.
  - `core/agent_loop.py:4327-4335` `_claim_coverage_status_label`이 `CONFLICT -> "정보 상충"`을 추가하고 `STRONG -> "교차 확인"`, `WEAK -> "단일 출처"`, fallback `-> "미확인"`을 그대로 유지합니다.
  - `core/agent_loop.py:4415-4419` `_build_claim_coverage_progress_summary`의 unresolved 집합이 `{CONFLICT, WEAK, MISSING}`로 확장되어, focus slot이 계속 CONFLICT일 때도 `"재조사했지만 ... 아직 정보 상충 상태입니다."`(라인 4460의 `f"재조사했지만 {slot}{focus_particle} 아직 {current_label} 상태입니다."`로 동적 조립) 경로에 남습니다.
  - `core/agent_loop.py:3729` `_build_entity_slot_probe_queries`의 가드가 `{CoverageStatus.WEAK, CoverageStatus.CONFLICT}`로 확장되어, compact primary claim이 있는 CONFLICT 슬롯도 기존 query_map 재사용으로 targeted probe query를 받습니다.
- focused rerun과 보조 검증이 모두 통과했습니다.
  - `python3 -m unittest tests.test_smoke -k coverage` → `Ran 12 tests`, `OK`
  - `python3 -m py_compile core/agent_loop.py tests/test_smoke.py` → 출력 없음, exit `0`
  - `git diff --check -- core/agent_loop.py tests/test_smoke.py` → 출력 없음, exit `0`
- 새 회귀 자체도 의미가 있습니다.
  - `tests/test_smoke.py:2148-2200`대 영역에 `_claim_coverage_status_label(CoverageStatus.CONFLICT) == "정보 상충"`, `STRONG > CONFLICT > WEAK > 그 외` rank 순서, CONFLICT 슬롯 probe query 회귀가 한 묶음으로 들어갔습니다.
  - `tests/test_smoke.py:2376-2400`에 focus slot이 CONFLICT를 유지할 때 progress summary가 `"정보 상충 상태"`를 포함해 unresolved 경로에 머무는지가 회귀로 고정됐습니다.
- /work가 명시한 untouched 영역도 현재 tree에서 실제로 그대로입니다.
  - `app/serializers.py:282-286` `claim_coverage_summary` dict는 여전히 `STRONG`/`WEAK`/`MISSING` 3개 키만 enumerate합니다. CONFLICT 카운터는 추가되지 않았고, /work가 명시한 대로 별도 후속 후보로 남아 있습니다.
  - 문서 wording 변경 없음. 이번 라운드 변경이 현재 shipped 문장을 즉시 틀리게 만드는 범위가 아니었습니다.

## 검증
- 직접 코드/테스트 대조
  - 대상: `core/agent_loop.py`, `tests/test_smoke.py`, 그리고 untouched 영역 확인용으로 `app/serializers.py`.
  - 결과: `/work`가 설명한 4개 분기 변경, focused regression 추가, 그리고 serializer/docs untouched 주장이 현재 tree와 일치함을 확인했습니다.
- `python3 -m unittest tests.test_smoke -k coverage`
  - 결과: `Ran 12 tests`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, exit `0`
- broader `tests.test_smoke` 전체, `tests.test_web_app`, Playwright, `make e2e-test`은 이번 verify에서 다시 돌리지 않았습니다.
  - 이유: 이번 `/work`는 browser-visible 계약(`app/static/app.js`의 `formatClaimCoverageCountSummary`, Playwright fixtures, `tests.test_web_app`의 `claim_coverage_summary` dict shape)이나 공유 helper를 바꾸지 않았습니다. focused 12-test coverage rerun + py_compile + diff-check가 현재 truth 판정에 충분했습니다.

## 남은 리스크
- `app/serializers.py`의 `claim_coverage_summary`는 여전히 `STRONG`/`WEAK`/`MISSING` 3개 키만 합산하므로, 외부 client(`app/static/app.js:3081`의 `formatClaimCoverageCountSummary`, `tests/test_web_app.py`의 8455/13869/13974/14088/14510 등 dict shape lock, `e2e/tests/web-smoke.spec.mjs`의 1806/1816/2106/2367/2516/2654 등 fixture)는 CONFLICT 슬롯을 카운트로 보지 못합니다. agent loop 내부에서는 CONFLICT가 별도 의미를 갖지만, 외부 payload/UI 경계는 아직 평탄화 상태입니다.
- agent_loop의 focus_slot improved/regressed 문장 분기는 이번 라운드에서 wording을 그대로 두고 unresolved membership과 label/rank만 통과시켰습니다. CONFLICT 전용 stronger explanation이나 reinvestigation trigger threshold 변경은 아직 없습니다.
- broad `tests.test_pipeline_gui_backend::TestRuntimeStatusRead` failure는 이번 라운드 범위 밖이고 별도 truth-sync 라운드 몫으로 dirty state에 남아 있습니다.
