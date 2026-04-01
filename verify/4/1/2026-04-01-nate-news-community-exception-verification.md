# 2026-04-01 news.nate.com community exception verification

## 변경 파일
- `verify/4/1/2026-04-01-nate-news-community-exception-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-nate-news-community-exception.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-daum-news-community-exception-verification.md`를 기준으로 이번 라운드 truth만 다시 확인할 필요가 있었습니다.
- 직전 `.pipeline/codex_feedback.md`의 `STATUS: needs_operator`는 `news.nate.com`과 `news.zum.com` 사이 tie를 이유로 멈춰 있었지만, 최신 `/work`가 이미 operator 결정과 `news.nate.com` 구현 완료를 기록하고 있어 current repo 기준으로 stale해졌습니다.

## 핵심 변경
- Claude가 주장한 이번 라운드 코드 변경은 실제로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py` 4개 파일에만 존재했습니다.
- `core/source_policy.py`와 `core/agent_loop.py`의 news host 예외 목록에 `news.nate.com`이 추가돼 현재 `news.nate.com`은 `news`로 분류됩니다.
- `tests/test_source_policy.py`에는 `news.nate.com -> news` 회귀가, `tests/test_web_app.py`에는 `news.nate.com + mk + noisy community` latest_update badge contract 회귀가 실제로 존재했습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 쪽 이번 라운드 추가 변경은 확인되지 않았고, 범위도 secondary web investigation의 `latest_update` source-classification same-family current-risk reduction 1건에 머물러 현재 `projectH` 방향을 벗어나지 않았습니다.
- 남은 same-family residual은 현재 local evidence 기준으로 `news.zum.com` 1건으로 좁혀져 `.pipeline/codex_feedback.md`를 다시 `STATUS: implement`로 올렸습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`: `Ran 178 tests in 3.395s`, `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`: 통과
- `rg -n "news\\.nate\\.com|news\\.zum\\.com|nate-news-community-exception" README.md docs tests/test_smoke.py core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py work/4/1/2026-04-01-nate-news-community-exception.md`: 이번 라운드의 `news.nate.com` 추가는 코드/테스트와 `/work`에만 확인됐고 `README.md`, `docs/`, `tests/test_smoke.py` 추가 변경은 없었습니다.
- 수동 spot-check:
- `https://news.nate.com/view/20260401n00123 -> news`
- `https://news.zum.com/articles/97600001 -> general`
- `https://news.daum.net/v/20260401120000001 -> news`
- `https://v.daum.net/v/20260401120000001 -> news`
- `https://news.naver.com/main/read.naver?oid=001&aid=0000001 -> news`
- 브라우저 계약 변경은 아니라 `make e2e-test`는 이번 라운드에 재실행하지 않았습니다.

## 남은 리스크
- 같은 family의 다음 current-risk reduction은 `news.zum.com` 1건입니다.
- dirty worktree는 여전히 넓으므로 다음 Claude 라운드도 지정된 4개 파일만 좁게 건드려야 합니다.
- whole-project audit 신호는 없어 `report/`는 만들지 않았습니다.
