# 2026-04-19 focus slot weak missing wording

## 변경 파일
- core/agent_loop.py
- tests/test_smoke.py

## 사용 skill
- release-check: handoff가 요구한 `tests.test_smoke` 중심 검증, `py_compile`, `git diff --check`, 추가 assertion grep 결과를 실제 실행 기준으로 정리했습니다.
- work-log-closeout: `/work` 표준 섹션 순서로 이번 bounded code slice의 실제 변경, 실제 검증, 남은 리스크만 기록했습니다.

## 변경 이유
- seq 385에서 focus-slot unresolved summary에 CONFLICT 전용 문장은 이미 들어갔지만, WEAK와 MISSING은 여전히 `아직 {current_label} 상태입니다`라는 generic fallback을 공유하고 있었습니다.
- 이번 handoff 목표는 그 generic fallback을 explicit Korean sentence 두 개로 분리해, WEAK는 "한 가지 출처 정보만 확인됨", MISSING은 "관련 정보를 찾지 못함"을 직접 드러내도록 바꾸는 것이었습니다.

## 핵심 변경
- `core/agent_loop.py:4465-4478`의 `_build_claim_coverage_progress_summary` focus-slot unresolved branch는 이제 WEAK일 때 정확히 `"재조사했지만 {slot}{focus_particle} 아직 한 가지 출처의 정보로만 확인됩니다."`, 그 외 unresolved fall-through(MISSING 포함)일 때 정확히 `"재조사했지만 {slot}{focus_particle} 아직 관련 정보를 찾지 못했습니다."`를 반환합니다.
- 같은 branch의 CONFLICT template `"재조사했지만 {slot}{focus_particle} 출처들이 서로 어긋난 채 남아 있습니다."`는 그대로 유지했습니다. unresolved bucket membership, particle selection, improved/regressed branch, `_claim_coverage_status_label`/rank/probe/source-role 관련 surface는 건드리지 않았습니다.
- `current_label`은 WEAK/MISSING return path에서 더 이상 소비되지 않지만, handoff 지시대로 `unresolved_slots.append((slot, self._claim_coverage_status_label(current_status), current_status))`의 3-tuple shape와 loop unpack(`for slot, current_label, cur_status in unresolved_slots`)는 그대로 보존했습니다.
- `tests/test_smoke.py`의 `test_build_claim_coverage_progress_summary_focus_slot_unresolved_wording_branches_by_status`에서 WEAK assertion은 `2672`의 `"재조사했지만 이용 형태는 아직 한 가지 출처의 정보로만 확인됩니다."`로, MISSING assertion은 `2678`의 `"재조사했지만 상태는 아직 관련 정보를 찾지 못했습니다."`로 뒤집었습니다. CONFLICT assertion은 그대로입니다.
- step 3 grep은 target test 외에 old WEAK generic wording에 기대는 live assertion 두 곳을 더 찾았습니다. `test_load_web_search_record_legacy_claim_coverage_slots_reload_surface_and_follow_up_progress_canonicalized`의 `tests/test_smoke.py:2557`과 `test_entity_reinvestigation_query_reports_claim_progress`의 `tests/test_smoke.py:3243-3245`를 새 WEAK wording 기준으로 조정했습니다. grep hit 중 `2738/2820/2899/3040`은 stored `claim_coverage_progress_summary` fixture literal이라 수정하지 않았습니다.
- 이번 라운드에서는 browser code, docs, 다른 test file, 다른 source file은 수정하지 않았습니다. `core/agent_loop.py`와 `tests/test_smoke.py`의 pre-existing unrelated dirty hunk는 유지했고, handoff가 지정한 wording branch와 smoke assertion만 추가로 수정했습니다.

## 검증
- `python3 -m unittest tests.test_smoke -k coverage`
  - 1차 실행 결과: `Ran 16 tests`, `FAILED (failures=1)`
  - 실패 테스트: `test_load_web_search_record_legacy_claim_coverage_slots_reload_surface_and_follow_up_progress_canonicalized`
  - 원인: live focus-slot summary가 `"단일 출처 상태"` 대신 새 WEAK explicit wording을 내보내는데 old assertion이 남아 있었습니다.
  - `tests/test_smoke.py:2557` / `:3243-3245` assertion sync 후 재실행 결과: `Ran 16 tests in 0.104s`, `OK`
- `python3 -m unittest tests.test_smoke -k claims`
  - 결과: `Ran 5 tests in 0.001s`, `OK`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `git diff --check -- core/agent_loop.py tests/test_smoke.py`
  - 결과: 출력 없음, 통과
- `rg -n -C 2 "아직 단일 출처 상태입니다|아직 미확인 상태입니다|한 가지 출처의 정보로만 확인됩니다|관련 정보를 찾지 못했습니다" tests/test_smoke.py`
  - 결과: 새 explicit wording은 `2557`, `2672`, `2678`, `3243-3245`에서 확인됐습니다.
  - old generic wording hit는 `2738`, `2820`, `2899`, `3040`의 stored `claim_coverage_progress_summary` fixture literal만 남았습니다. focus-slot live assertion 추가 조정 대상은 더 없었습니다.
- Playwright는 실행하지 않았습니다. 이번 슬라이스는 server-emitted Korean sentence와 Python smoke assertion만 바꾸며 shared browser helper나 browser-visible contract 범위를 넓히지 않습니다.
- `python3 -m unittest tests.test_web_app`와 `make e2e-test`도 실행하지 않았습니다. 둘 다 이번 slice 밖입니다.

## 남은 리스크
- `docs/PRODUCT_SPEC.md:369`와 `docs/ACCEPTANCE_CRITERIA.md:35`에는 stored `claim_coverage_progress_summary` normalization clause 안에 여전히 `재조사했지만 ... 아직 단일 출처 상태입니다` 예시가 남아 있습니다. 이번 라운드는 docs를 건드리지 않았고, 이 문구가 legacy stored-progress/read-time canonicalization 예시로 계속 truthful한지 여부는 별도 narrow docs-sync round에서 다시 확인해야 합니다.
- Milestone 4의 remaining candidate로 COMMUNITY/PORTAL/BLOG weighting, response-body `[정보 상충]` tag emission, 추가 reinvestigation tuning은 여전히 separate future code round 후보입니다.
- unrelated full `python3 -m unittest tests.test_web_app` failure family는 이번 handoff 범위 밖으로 그대로 남아 있습니다.
