# 2026-03-31 latest-update verification_label reload parity

## 변경 파일
- `core/agent_loop.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 `B: latest_update answer-mode noise filtering` family에서 `verification_label`이 reload 후에도 stored single-source truth를 유지하도록 잠그기 지시.
- 뉴스 1건 + noisy community 1건 fixture에서 initial 응답은 `"단일 출처 참고"`인데 `load_web_search_record_id` reload 후 `"다중 출처 참고"`로 올라가는 bug 확인.

## 핵심 변경
- `_build_web_search_origin` fix (`core/agent_loop.py`)
  - `verification_label` 산출에 `selected_sources`(필터 전) 대신 `role_sources`(noisy source 제외 후)를 전달하도록 수정
  - entity_card와 latest_update 모두에 적용 (같은 `role_sources` 변수 사용)
- `test_handle_chat_latest_update_single_source_verification_label_retained_after_history_card_reload` 추가 (`tests/test_web_app.py`)
  - fixture: 뉴스 1건 + noisy community 1건 (brunch.co.kr)
  - 첫 응답: `verification_label == "단일 출처 참고"` 확인
  - history badge: 동일 label 확인
  - `load_web_search_record_id` reload: 동일 label parity 확인

## 검증
- `python3 -m unittest -v tests.test_web_app`: 127 tests, OK (2.659s)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`: 통과

## 남은 리스크
- `verification_label`이 `role_sources`(필터 후)를 사용하므로 entity_card 경로에서도 동일 변경이 적용됨. 기존 entity_card 테스트 127개 전부 통과했으므로 regression은 없음.
- latest_update noisy source filtering family: initial + 자연어 reload + history-card reload + verification_label parity 모두 잠김.
- dirty worktree가 여전히 넓음.
