# 2026-03-31 hankyung.com news domain coverage verification

## 변경 파일
- `verify/3/31/2026-03-31-hankyung-news-domain-coverage-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-hankyung-news-domain-coverage.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-latest-update-verification-label-reload-parity-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 latest_update answer-mode의 real news-domain coverage를 `hankyung.com` 1건으로 올리고, 그 결과 `기사 2건 + noisy community 1건` fixture의 badge/source-role contract를 잠갔다고 적고 있으므로, 이번 검수에서는 그 domain hint 추가와 regression이 실제로 들어갔는지, 검증 자기보고가 맞는지, docs 무변경이 round-local로 truthful한지만 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 주장은 사실입니다. [`core/source_policy.py`](/home/xpdlqj/code/projectH/core/source_policy.py#L43)에 `hankyung.com`이 news-domain hint로 실제 추가되어 있고, [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L2807) 의 `_classify_web_source_kind`에도 같은 hint가 반영되어 source-type/source-kind 판정이 맞춰졌습니다.
- 테스트 보강도 실제로 들어갔습니다. [`tests/test_source_policy.py#L9`](/home/xpdlqj/code/projectH/tests/test_source_policy.py#L9) 에 `hankyung.com -> news` assertion이 추가되었고, [`tests/test_web_app.py#L9803`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9803) 의 `test_handle_chat_latest_update_dual_news_noisy_community_badge_contract`는 `hankyung + mk + brunch` fixture에서 첫 응답, history badge, `load_web_search_record_id` reload의 `기사 교차 확인` 유지와 generic `보조 출처` 미노출을 실제로 잠급니다.
- `/work`의 검증 자기보고도 사실입니다. `python3 -m unittest -v tests.test_source_policy tests.test_web_app`를 다시 돌려 `Ran 131 tests in 3.231s`, `OK`를 확인했고, `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`도 통과했습니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 secondary web investigation의 latest_update source classification coverage 1건에 그쳤고, ranking rewrite, docs wording change, entity-card family 재작업, browser-visible UI 구조 변경은 섞이지 않았습니다.
- docs 무변경도 이번 round-local 범위에서는 truthful합니다. `stat` 기준 [`README.md`](/home/xpdlqj/code/projectH/README.md), [`docs/PRODUCT_SPEC.md`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md), [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md)는 모두 latest `/work`보다 앞선 수정 시각이며, 이번 라운드는 기존 source-role / verification-label contract의 coverage 보정이지 새 문서 문구를 요구하는 contract 확대는 아니었습니다.
- 추가 확인: latest `/work`가 예시로만 남긴 후속 후보 중 `etnews.com`은 이미 `news`로 분류되지만, `edaily.co.kr`는 아직 `general`입니다. 수동 fixture replay에서 `edaily + mk + brunch` latest_update는 initial/history/`load_web_search_record_id` reload 모두 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`로 남아, 같은 answer-mode 주변의 다음 smallest user-visible downgrade가 현재는 `edaily.co.kr` coverage임을 확인했습니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_source_policy tests.test_web_app`
  - 통과 (`Ran 131 tests in 3.231s`, `OK`)
- `git diff --check -- core/source_policy.py core/agent_loop.py tests/test_source_policy.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-hankyung-news-domain-coverage.md`
  - `verify/3/31/2026-03-31-latest-update-verification-label-reload-parity-verification.md`
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
  - `classify_source_type('https://www.edaily.co.kr/News/Read?newsId=123') -> general`
  - `classify_source_type('https://www.etnews.com/20260331000123') -> news`
  - `edaily + mk + brunch` latest_update fixture에서 initial/history/`load_web_search_record_id` reload 모두 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`

## 남은 리스크
- latest `/work`가 겨냥한 `hankyung.com` latest_update badge downgrade는 이번 라운드로 truthfully 닫혔습니다.
- 같은 answer-mode 주변의 다음 smallest user-visible improvement는 `edaily.co.kr` coverage입니다. 현재는 `edaily`가 여전히 general로 분류되어 기사 2건 latest_update도 generic badge/source-role로 내려갑니다.
- 다음 라운드는 domain sweep을 넓히기보다, `edaily.co.kr` 1건만 추가해 `latest_update` badge/source-role contract를 같은 방식으로 한 칸 더 올리는 작은 source-classification slice가 적절합니다.
