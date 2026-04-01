# 2026-03-31 multi-source agreement over noise natural reload lock

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 multi-source agreement / single-source noise family에서 자연어 recent-record reload 경로를 잠그도록 지시.
- history-card `load_web_search_record_id` 경로는 이전 라운드에서 truthfully 닫혔고, 남은 same-family current-risk는 자연어 reload 경로뿐이었음.

## 핵심 변경
- `test_handle_chat_entity_card_multi_source_agreement_over_noise_natural_reload` 추가 (`tests/test_web_app.py`)
  - fixture: wiki 2개 (나무위키 + 위키백과) + noisy blog source 1개 (boilerplate 페이지, "출시일"/"2025" 고유 claim)
  - 첫 호출: entity-card 검색
  - 둘째 호출: `"방금 검색한 결과 다시 보여줘"` 자연어 reload
  - 첫 응답 assertion: `사실 카드:` + `교차 확인` 유지, `출시일`/`2025` 미노출
  - reload assertion: `사실 카드:` + `교차 확인` 유지, `출시일`/`2025` 미노출
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 124 tests, OK (2.345s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- multi-source agreement / single-source noise family는 history-card reload + 자연어 reload 두 경로 모두 agreement-over-noise를 explicit assertion으로 잠금. 이 family는 닫힘.
- dirty worktree가 여전히 넓음.
