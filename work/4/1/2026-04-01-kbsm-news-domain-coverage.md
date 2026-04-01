# 2026-04-01 kbsm.net news domain coverage

## 변경 파일
- `core/source_policy.py`
- `core/agent_loop.py`
- `tests/test_source_policy.py`
- `tests/test_web_app.py`

## 사용 skill
- 없음

## 변경 이유
- `.pipeline/codex_feedback.md`가 `STATUS: implement`로, 같은 `latest_update news-domain coverage` family에서 `kbsm.net`을 news domain으로 인식시키도록 지시.
- 이전 라운드에서 `idaebae.com` coverage가 truthfully 닫혔고, `kbsm.net`이 같은 family의 다음 smallest current-risk reduction.

## 핵심 변경
- `classify_source_type` news_host_hints에 `"kbsm.net"` 추가 (`core/source_policy.py`)
- `_classify_web_source_kind` news_host_hints에 `"kbsm.net"` 추가 (`core/agent_loop.py`)
- `test_classify_source_type_maps_known_domains`에 kbsm.net → news assertion 추가 (`tests/test_source_policy.py`)
- `test_handle_chat_latest_update_kbsm_mk_noisy_community_badge_contract` 추가 (`tests/test_web_app.py`)
  - fixture: KBSM 기사 + mk 기사 + noisy community (brunch.co.kr)
  - 첫 응답 + history badge + reload: `보조 출처` 미포함, `verification_label == "기사 교차 확인"`

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: 162 tests, OK (3.163s)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과

## 남은 리스크
- `kbsm.net` 1건만 추가. 같은 family에 미분류 news domain이 더 남아 있을 수 있음.
- dirty worktree가 여전히 넓음.
