# 2026-03-31 heraldcorp.com news domain coverage verification

## 변경 파일
- `verify/3/31/2026-03-31-heraldcorp-news-domain-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-heraldcorp-news-domain-coverage.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-etoday-news-domain-coverage-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 latest_update answer-mode의 real news-domain coverage를 `heraldcorp.com` 1건 더 올리고, `herald + mk + noisy community` fixture의 badge/source-role contract를 잠갔다고 적고 있으므로, 이번 검수에서는 그 domain hint 추가와 regression이 실제로 들어갔는지, 검증 자기보고가 맞는지, docs 무변경이 round-local로 truthful한지만 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 주장은 사실입니다. `core/source_policy.py`의 `classify_source_type(...)` news-domain hint와 `core/agent_loop.py`의 `_classify_web_source_kind(...)` news-domain hint에 `heraldcorp.com`이 실제 추가되어 source-type/source-kind 판정이 맞춰졌습니다.
- 테스트 보강도 실제로 들어갔습니다. `tests/test_source_policy.py`에는 `classify_source_type("https://news.heraldcorp.com/view/2025") == "news"` assertion이 추가되었고, `tests/test_web_app.py`의 `test_handle_chat_latest_update_herald_mk_noisy_community_badge_contract`는 `herald + mk + brunch` fixture에서 첫 응답, history badge, `load_web_search_record_id` reload의 `기사 교차 확인` 유지와 generic `보조 출처` 미노출을 실제로 잠급니다.
- `/work`의 검증 자기보고도 사실입니다. `python3 -m unittest -v tests.test_source_policy tests.test_web_app`를 다시 돌려 `Ran 134 tests in 2.996s`, `OK`를 확인했고, `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`도 통과했습니다. 실행 시간은 `/work`의 2.617s와 다르지만 테스트 수와 통과 여부는 일치합니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 secondary web investigation의 latest_update source classification coverage 1건에 그쳤고, ranking rewrite, broader answer-mode rewrite, docs wording change, browser-visible UI 구조 변경은 섞이지 않았습니다.
- docs 무변경도 이번 round-local 범위에서는 truthful합니다. `stat` 기준 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/NEXT_STEPS.md`는 모두 latest `/work`보다 앞선 수정 시각이며, 이번 라운드는 기존 latest_update badge/source-role contract의 coverage 보정이지 문서 contract 확대가 아니었습니다.
- 추가 확인: 같은 latest_update news-domain coverage family의 다음 user-visible downgrade도 좁게 재현했습니다. `classify_source_type("https://zdnet.co.kr/view/?no=20260331000123")`는 아직 `general`이고, `zdnet + mk + brunch` latest_update fixture도 initial/history/`load_web_search_record_id` reload 전부 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`로 남습니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - 통과 (`Ran 134 tests in 2.996s`, `OK`)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-heraldcorp-news-domain-coverage.md`
  - `verify/3/31/2026-03-31-etoday-news-domain-coverage-verification.md`
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
  - `classify_source_type('https://zdnet.co.kr/view/?no=20260331000123') -> general`
  - `classify_source_type('https://www.mk.co.kr/economy/2025') -> news`
  - `zdnet + mk + brunch` latest_update fixture에서 initial/history/`load_web_search_record_id` reload 모두 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`

## 남은 리스크
- latest `/work`가 겨냥한 `heraldcorp.com` latest_update badge downgrade는 이번 라운드로 truthfully 닫혔습니다.
- 같은 family의 다음 smallest user-visible improvement는 `zdnet.co.kr` coverage 1건입니다. 현재는 `zdnet.co.kr`가 여전히 general로 분류되어 기사 2건 latest_update도 generic badge/source-role로 내려갑니다.
- 이번 흐름은 도메인 sweep 전체가 아니라, current latest_update source-classification family의 한 칸짜리 coverage를 계속 좁게 올리는 쪽이 맞습니다.
