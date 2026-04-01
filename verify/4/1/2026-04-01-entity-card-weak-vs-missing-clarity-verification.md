## 변경 파일
- `verify/4/1/2026-04-01-entity-card-weak-vs-missing-clarity-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-entity-card-weak-vs-missing-clarity.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-web-search-reload-follow-up-response-origin-retention-verification.md`를 기준으로, 이번 라운드 주장만 좁게 검수해야 했습니다.
- 이번 라운드는 secondary web investigation의 entity-card 본문에서 weak single-source slot과 unresolved missing slot의 user-visible copy를 더 분명히 구분하는 작은 품질 개선 1건이었습니다.

## 핵심 변경
- Claude `/work` 주장대로 현재 코드의 실질 변경 지점은 `core/agent_loop.py`, `tests/test_smoke.py`, `tests/test_web_app.py` 3개 파일에 맞습니다.
- `core/agent_loop.py`
  - weak slot 섹션 헤더가 `단일 출처 확인 정보:`로 바뀌어, 단일 출처 확인 사실이라는 성격이 현재 문구에 반영돼 있습니다.
  - missing slot 섹션 헤더가 `아직 확인되지 않은 항목:`으로 바뀌어, unresolved slot이 단일 출처 weak slot과 분리됩니다.
  - missing slot 설명도 `교차 확인 가능한 근거를 찾지 못했습니다.`로 현재 상태 서술에 맞게 바뀌어 있습니다.
- `tests/test_smoke.py`
  - `test_web_search_entity_summary_marks_unresolved_slots_when_claim_support_is_weak`가 새 weak/missing 문구와 unresolved slot 설명을 직접 검증합니다.
- `tests/test_web_app.py`
  - `test_handle_chat_entity_card_separates_weak_and_missing_slot_sections`
  - `test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_history_card_reload`
  - `test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_natural_reload`
  - 위 3경로가 실제로 존재하며, `/work`가 말한 첫 응답, history-card reload, 자연어 recent-record reload 범위를 맞게 덮고 있습니다.
- 파일 시각 대조 결과, 이번 handoff 직전 `.pipeline/codex_feedback.md` 이후 `work` note가 기록되기 전 tracked 소스 파일 변경은 위 3개뿐이었습니다. 같은 시간대의 추가 파일은 `__pycache__`와 test run이 만든 local `data/web-search/` 산출물뿐이라 `/work`의 round-local 범위 주장은 현재 상태와 충돌하지 않았습니다.
- `README.md`, `docs/PRODUCT_SPEC.md`는 이번 `/work`보다 이른 시각 파일이며, root docs에는 해당 exact copy가 기록돼 있지 않아 docs 미수정 주장도 현재 truth와 맞습니다. 예전 표현은 `docs/recycle/` 초안에만 남아 있습니다.
- 범위 역시 source ranking, taxonomy, `claim_coverage` schema 변경으로 넓어지지 않고 entity-card copy clarity 1건에 머물러 현재 `projectH`의 document-first MVP 및 secondary web investigation hardening 방향을 벗어나지 않았습니다.

## 검증
- 첫 재실행 시도
  - `python3 -m unittest -v tests.test_smoke.AgentLoopTestCase.test_web_search_entity_summary_marks_unresolved_slots_when_claim_support_is_weak tests.test_web_app.WebAppServiceTestCase.test_handle_chat_entity_card_separates_weak_and_missing_slot_sections tests.test_web_app.WebAppServiceTestCase.test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_history_card_reload tests.test_web_app.WebAppServiceTestCase.test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_natural_reload`
  - 실패: 존재하지 않는 클래스명 `AgentLoopTestCase`, `WebAppServiceTestCase`를 지정해 unittest loader error가 발생했습니다.
- 실제 통과한 재실행
  - `python3 -m unittest -v tests.test_smoke.SmokeTest.test_web_search_entity_summary_marks_unresolved_slots_when_claim_support_is_weak tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_separates_weak_and_missing_slot_sections tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_history_card_reload tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_weak_vs_missing_slot_retained_after_natural_reload`
  - 결과: `Ran 4 tests in 0.072s`, `OK`
- `git diff --check -- core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
  - 통과
- 코드/문서 truth 대조
  - `sed`로 `core/agent_loop.py`, `tests/test_smoke.py`, `tests/test_web_app.py`의 weak/missing section 본문 확인
  - `rg`로 root docs와 운영 문서에 exact copy가 박혀 있지 않은 점 확인
  - `stat`, `find -newermt`로 이번 round-local 변경 파일 범위 확인
- 이번 변경은 copy-level service/browser contract 확인으로 충분해 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- 이번 Claude `/work` 주장은 현재 파일 상태와 재실행 검증 기준으로 사실이었습니다.
- weak single-source slot vs unresolved missing slot clarity family는 service/API 레벨 기준으로 truthfully 닫혔습니다.
- 남은 것은 주로 verification-strength gap 또는 다른 investigation quality axis입니다.
  - 예: 새 문구에 대한 browser smoke 직접 고정
  - 예: 다른 entity-card quality slice
- 다만 이것만으로 다음 단일 슬라이스를 자동 확정하기엔 근거가 부족해, 이번 handoff는 `.pipeline/codex_feedback.md`를 `STATUS: needs_operator`로 내리는 편이 더 정직합니다.
- dirty worktree가 여전히 넓어 다음 구현 라운드에서도 범위 고정이 계속 필요합니다.
