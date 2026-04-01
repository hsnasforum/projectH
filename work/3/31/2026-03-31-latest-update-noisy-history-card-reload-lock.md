# 2026-03-31 latest-update noisy history-card reload lock

## 변경 파일
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 `B: latest_update answer-mode noise filtering` family에서 history-card `load_web_search_record_id` reload 경로를 잠그도록 지시.
- initial 응답 + 자연어 reload는 이전 라운드에서 잠겼고, 남은 same-family current-risk는 history-card reload 경로뿐이었음.

## 핵심 변경
- `test_handle_chat_latest_update_noisy_source_excluded_after_history_card_reload` 추가 (`tests/test_web_app.py`)
  - fixture: 뉴스 2개 + noisy community source 1개 (brunch.co.kr, boilerplate snippet)
  - 첫 호출: latest_update 검색, record_id 추출
  - 둘째 호출: `load_web_search_record_id` reload
  - assertion: `answer_mode == "latest_update"` 유지, `보조 커뮤니티` role 미노출, `brunch` URL 본문 미노출
- production 코드 변경 없음 — test-only slice

## 검증
- `python3 -m unittest -v tests.test_web_app`: 126 tests, OK (2.537s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- latest_update noisy source filtering family: initial 응답 + 자연어 reload + history-card reload 3개 경로 모두 잠김. 이 family는 닫힘.
- dirty worktree가 여전히 넓음.
