# 2026-03-31 edaily.co.kr news domain coverage

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 `B: latest_update answer-mode noise filtering` family에서 `edaily.co.kr`를 news domain으로 인식시켜 latest_update badge가 generic `보조 출처` / `다중 출처 참고`로 내려가지 않도록 잠그기 지시.

## 핵심 변경
- `classify_source_type` news_host_hints에 `"edaily.co.kr"` 추가 (`core/source_policy.py`)
- `_classify_web_source_kind` news_host_hints에 `"edaily.co.kr"` 추가 (`core/agent_loop.py`)
- `test_classify_source_type_maps_known_domains`에 edaily.co.kr → news assertion 추가 (`tests/test_source_policy.py`)
- `test_handle_chat_latest_update_edaily_mk_noisy_community_badge_contract` 추가 (`tests/test_web_app.py`)
  - fixture: edaily 기사 + mk 기사 + noisy community (brunch.co.kr)
  - 첫 응답: `보조 출처` 미포함, `verification_label == "기사 교차 확인"`
  - history badge: 동일 label
  - `load_web_search_record_id` reload: 동일 label parity

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 132 tests, OK (3.171s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- `edaily.co.kr` 1건만 추가. 다른 미분류 한국 경제지 domain이 남아 있을 수 있음.
- dirty worktree가 여전히 넓음.
