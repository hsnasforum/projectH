## 변경 파일
- `verify/4/1/2026-04-01-generic-news-substring-false-positive-reduction-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-generic-news-substring-false-positive-reduction.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-web-search-broader-news-noise-host-sweep-verification.md`를 기준으로 이번 라운드 주장만 다시 검수해야 했습니다.
- 이번 라운드는 generic `"news"` substring false-positive family가 실제 코드에서 이미 닫혀 있었는지, 그리고 이번 변경이 그 상태를 focused regression으로만 보강한 것인지 확인하는 것이 핵심이었습니다.

## 핵심 변경
- Claude 주장대로 current file state 기준 이번 라운드의 실질 추가 변경은 `tests/test_source_policy.py` 쪽 focused regression 보강으로 보였고, 새 코드 로직 추가는 확인되지 않았습니다.
- `core/source_policy.py`는 현재 explicit `news_domain_hosts` exact-or-subdomain boundary만 사용하며, bare `"news"` substring catch-all은 남아 있지 않았습니다.
- `tests/test_source_policy.py`에는 `fakenews.co.kr -> general`, `mynewssite.com -> general` assertion이 실제로 추가되어 있었고, 기존 `unknownlocalnews.kr -> general`, `news.example.com -> general` guard도 유지되어 있었습니다.
- `tests/test_web_app.py`의 latest-update badge regression은 이번 라운드에서 새로 늘어나지 않았고, current file state에서는 기존 `unknownlocalnews.kr` / `news.example.com` guard만 유지되고 있었습니다.
- local mtime evidence도 `/work` 주장과 대체로 맞았습니다.
  - `core/source_policy.py`: `2026-04-01 01:47:47 +0900`
  - `tests/test_web_app.py`: `2026-04-01 01:48:54 +0900`
  - `tests/test_source_policy.py`: `2026-04-01 02:25:17 +0900`
  - latest `/work`: `2026-04-01 02:25:43 +0900`
  - 즉 latest `/work` 시점 직전 갱신 흔적은 `tests/test_source_policy.py`에만 보이고, core/test_web_app 쪽은 earlier same-day 상태와 일치했습니다.
- `README.md`, `docs/*`, `tests/test_smoke.py`에는 이번 slug나 관련 false-positive host를 직접 언급하는 round-local 추가 변경이 보이지 않았습니다.
- 범위도 source classification false-positive guard family 안에 머물러 현재 `projectH` 방향을 벗어나지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy`
  - `Ran 3 tests in 0.002s`
  - `OK`
- `git diff --check -- core/source_policy.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과
- `rg -n 'generic "news" substring false-positive reduction|fakenews\\.co\\.kr|mynewssite\\.com|unknownlocalnews\\.kr|news\\.example\\.com' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/NEXT_STEPS.md docs/PRODUCT_SPEC.md docs/TASK_BACKLOG.md tests/test_smoke.py`
  - 결과 없음
- 수동 spot-check
  - `https://fakenews.co.kr/article/1 => general`
  - `https://mynewssite.com/article/1 => general`
  - `https://www.unknownlocalnews.kr/article/1 => general`
  - `https://news.example.com/article => general`
  - `https://www.newsis.com/view/NISX20260401_0001 => news`
  - `https://news.naver.com/main/read.naver?oid=001&aid=0000001 => news`
  - `https://www.news1.kr/articles/?5000001 => news`
- browser-visible contract 변경은 아니라 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- latest `/work`의 핵심 주장은 current code/test state 기준으로는 대체로 사실이었습니다. 이번 라운드는 새 코드 로직을 여는 것이 아니라 이미 닫힌 false-positive family를 focused regression으로 더 잠근 쪽에 가까웠습니다.
- 즉 generic `"news"` substring false-positive family 자체는 current source classification contract에서 사실상 닫힌 상태로 보입니다.
- 따라서 다음 자동 구현 슬라이스를 같은 family 안에서 더 좁게 고정할 근거는 현재 local evidence만으로는 약합니다.
- 남은 후보는 예를 들면:
  - `core/source_policy.py`, `core/agent_loop.py`, `tools/web_search.py` host registry를 single source-of-truth로 정리하는 internal cleanup
  - source classification / page-text refinement와 별개인 다른 current-risk 또는 user-visible quality axis
- 위 이유로 이번 라운드 이후 `.pipeline/codex_feedback.md`는 `STATUS: needs_operator`로 두는 편이 현재 truth에 맞습니다.
- 이번 검수는 latest Claude round truth 확인과 next-step truth-sync에 한정했습니다. whole-project audit 징후는 없어 `report/`는 만들지 않았습니다.
