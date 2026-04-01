## 변경 파일
- `verify/4/1/2026-04-01-broader-news-domain-sweep-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 Claude `/work`인 `work/4/1/2026-04-01-broader-news-domain-sweep.md`와 같은 날 최신 `/verify`인 `verify/4/1/2026-04-01-joongdo-news-domain-coverage-verification.md`를 기준으로, 이번 라운드가 주장한 broader same-family news-domain sweep이 실제 코드/테스트와 맞는지 좁게 재검증할 필요가 있었습니다.

## 핵심 변경
- Claude `/work` 주장대로 `core/source_policy.py`, `core/agent_loop.py`, `tests/test_source_policy.py`, `tests/test_web_app.py`의 4개 파일에 same-family source-classification 변경이 집중돼 있음을 확인했습니다.
- `tests/test_source_policy.py`에는 `dynews.co.kr`, `ccdailynews.com`, `jbnews.com`, `gjdream.com`, `jejunews.com`, `headlinejeju.co.kr`, `ohmynews.com`, `pressian.com`, `nocutnews.co.kr`, `newsis.com`, `news1.kr`, `mbn.co.kr`, `sbs.co.kr`, `kbs.co.kr`, `ytn.co.kr`, `jtbc.co.kr`, `ichannela.com`, `tvchosun.com`, `etnews.com`, `bloter.net`에 대한 assertion이 실제로 존재했습니다.
- `tests/test_web_app.py`에는 대표 badge regression인 `test_handle_chat_latest_update_newsis_mk_noisy_community_badge_contract`가 실제로 존재했습니다.
- `README.md`, `docs/`, `tests/test_smoke.py` 계열에는 이번 라운드용 추가 변경이 없었고, round-local 문서 무변경 주장도 맞았습니다.
- 다만 `/work` closeout의 `"21건"` 표기는 현재 note 안에 실제로 나열된 도메인과 코드상 새 explicit domain 묶음 기준으로는 `20건`이어서, closeout 수치 설명은 1건 과장돼 있었습니다.
- 이번 변경은 automatic one-domain slice를 넘어선 broader same-family sweep이지만, 여전히 secondary web investigation의 `latest_update` source-classification family 안에 머물러 현재 document-first MVP 방향 자체를 벗어나지는 않았습니다.
- 새 검수 결과를 기준으로 `.pipeline/codex_feedback.md`는 임의 residual domain 지정보다 현재 확인된 false-positive risk를 줄이는 exact next slice로 갱신했습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - `Ran 172 tests in 3.063s`
  - `OK`
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과
- 수동 spot-check
  - `classify_source_type("https://www.newsis.com/view/NISX20260401_000000001") == "news"`
  - `classify_source_type("https://www.news1.kr/society/general-news/1234567") == "news"`
  - `classify_source_type("https://news.sbs.co.kr/news/endPage.do?news_id=N100000001") == "news"`
  - `classify_source_type("https://www.etnews.com/20260401000001") == "news"`
  - `classify_source_type("https://www.bloter.net/news/articleView.html?idxno=123456") == "news"`
  - `classify_source_type("https://www.unknownlocalnews.kr/article/1") == "news"`
- 문서/비범위 파일 spot-check
  - `rg -n "newsis|news1.kr|mbn.co.kr|sbs.co.kr|kbs.co.kr|ytn.co.kr|jtbc.co.kr|ichannela.com|tvchosun.com|etnews.com|bloter.net|ohmynews.com|pressian.com|nocutnews.co.kr|gjdream.com|jejunews.com|headlinejeju.co.kr" README.md docs tests/test_smoke.py`
  - `README.md`, `docs/`, `tests/test_smoke.py`에는 이번 sweep용 추가 변경 없음
- 미실행 검증
  - 브라우저 계약 변경이 아니라서 `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- 현재 분류 로직은 bare `"news"` substring hint를 유지하고 있어, `unknownlocalnews.kr` 같은 미등록 hostname도 `news`로 오인 분류합니다. 이번 broader sweep으로 explicit domain coverage는 넓어졌지만, false-positive risk는 그대로 남아 있습니다.
- 따라서 다음 자동 슬라이스는 another domain batch보다, generic `"news"` hint를 줄여도 explicit major-domain coverage가 유지되는지 잠그는 current-risk reduction이 더 맞습니다.
- `/work` closeout의 `"21건"` 표기는 코드 truth보다 1건 크게 적혀 있으므로, 다음 closeout에서는 수치 설명을 실제 리스트와 맞춰 적는 편이 좋습니다.
- 이번 note는 latest Claude round truth 검수와 다음 단일 슬라이스 지정까지만 다룹니다. whole-project audit이 필요한 징후는 확인되지 않아 `report/`는 만들지 않았습니다.
