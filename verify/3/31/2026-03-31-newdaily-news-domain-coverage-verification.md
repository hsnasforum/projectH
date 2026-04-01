# 2026-03-31 newdaily.co.kr news domain coverage verification

## 변경 파일
- `verify/3/31/2026-03-31-newdaily-news-domain-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-newdaily-news-domain-coverage.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-seoul-news-domain-coverage-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 `biz.newdaily.co.kr`를 news domain으로 승격하고 `newdaily + mk + noisy community` latest_update badge contract를 잠갔다고 적고 있으므로, 이번 검수에서는 그 domain hint 추가와 regression이 실제로 들어갔는지, 검증 자기보고가 맞는지, docs 무변경이 round-local로 truthful한지만 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 구현 주장은 사실입니다. `core/source_policy.py`의 `classify_source_type(...)` news-domain hint와 `core/agent_loop.py`의 `_classify_web_source_kind(...)` news-domain hint에 `newdaily.co.kr`가 실제 추가되어 `biz.newdaily.co.kr`가 `news`로 분류됩니다.
- 테스트 보강도 실제로 들어갔습니다. `tests/test_source_policy.py`에는 `classify_source_type("https://biz.newdaily.co.kr/news/2025") == "news"` assertion이 추가되어 있고, `tests/test_web_app.py`의 `test_handle_chat_latest_update_newdaily_mk_noisy_community_badge_contract`는 `newdaily + mk + brunch` fixture에서 첫 응답, history badge, `load_web_search_record_id` reload의 `기사 교차 확인` 유지와 generic `보조 출처` 미노출을 잠급니다.
- `/work`의 검증 자기보고도 사실입니다. `python3 -m unittest -v tests.test_source_policy tests.test_web_app`를 다시 돌려 `Ran 138 tests in 2.817s`, `OK`를 확인했고, `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`도 통과했습니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 secondary web investigation의 latest_update source classification coverage 1건에 그쳤고, ranking rewrite, browser-visible UI 구조 변경, broader answer-mode rewrite, docs wording change는 섞이지 않았습니다.
- docs 무변경도 이번 round-local 범위에서는 truthful합니다. `stat` 기준 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`는 모두 latest `/work`보다 앞선 수정 시각이며, 이번 라운드는 기존 latest_update badge/source-role contract의 coverage 보정이지 새 문서 문구를 요구하는 contract 확대는 아니었습니다.
- 다만 `/work`의 남은 리스크 문구 중 `한국 주요 뉴스/경제지 domain coverage는 대부분 닫힌 상태`는 현재 truth보다 약간 앞섭니다. 수동 spot-check에서 `moneytoday.co.kr`와 `segye.com`은 아직 `general`이고, `moneytoday + mk + brunch` latest_update fixture는 first response, history, `load_web_search_record_id` reload 모두 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`로 남습니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - 통과 (`Ran 138 tests in 2.817s`, `OK`)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-newdaily-news-domain-coverage.md`
  - `verify/3/31/2026-03-31-seoul-news-domain-coverage-verification.md`
  - `.pipeline/codex_feedback.md`
  - `core/source_policy.py`
  - `core/agent_loop.py`
  - `tests/test_source_policy.py`
  - `tests/test_web_app.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/NEXT_STEPS.md`
- 추가 수동 재현
  - `classify_source_type('https://biz.newdaily.co.kr/site/data/html/2026/03/31/20260331000123.html') -> news`
  - `classify_source_type('https://www.moneytoday.co.kr/news/202603310001') -> general`
  - `classify_source_type('https://www.segye.com/newsView/202603310001') -> general`
  - `moneytoday + mk + brunch` latest_update fixture에서 first/history/`load_web_search_record_id` reload 모두 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`

## 남은 리스크
- latest `/work`가 겨냥한 `biz.newdaily.co.kr` latest_update badge downgrade는 이번 라운드로 truthfully 닫혔습니다.
- 같은 family의 다음 smallest user-visible improvement는 `moneytoday.co.kr` coverage 1건입니다. 현재는 `moneytoday.co.kr`가 여전히 `general`로 분류되어 기사 2건 latest_update도 generic badge/source-role로 내려갑니다.
- 다음 라운드는 domain sweep을 넓히기보다, `moneytoday.co.kr` 1건만 추가해 `latest_update` badge/source-role contract를 같은 방식으로 한 칸 더 올리는 작은 source-classification slice가 적절합니다.
