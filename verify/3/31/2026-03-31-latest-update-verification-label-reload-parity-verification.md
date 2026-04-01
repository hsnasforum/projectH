# 2026-03-31 latest-update verification_label reload parity verification

## 변경 파일
- `verify/3/31/2026-03-31-latest-update-verification-label-reload-parity-verification.md`
- `.pipeline/codex_feedback.md`

## 사용 skill
- `round-handoff`
- `investigation-quality-audit`

## 변경 이유
- 사용자 요청에 따라 `AGENTS.md`, `work/README.md`, `verify/README.md`, `.pipeline/README.md`를 먼저 다시 읽고, latest Claude `/work`인 `work/3/31/2026-03-31-latest-update-verification-label-reload-parity.md`와 같은 날 latest `/verify`인 `verify/3/31/2026-03-31-latest-update-noisy-history-card-reload-lock-verification.md`를 기준으로 이번 라운드 주장만 좁게 검수해야 했습니다.
- latest `/work`는 같은 `B: latest_update answer-mode noise filtering` family에서 `load_web_search_record_id` history-card reload 후에도 single-source noisy fixture의 `verification_label` parity를 유지하도록 production fix 1건과 regression 1건을 넣었다고 적고 있으므로, 이번 검수에서는 그 코드/테스트가 실제로 들어갔는지, 검증 자기보고가 맞는지, 그리고 범위가 current `projectH` 방향을 벗어나지 않았는지만 확인하면 충분했습니다.

## 핵심 변경
- 판정: latest `/work`의 핵심 주장은 사실입니다. [`core/agent_loop.py`](/home/xpdlqj/code/projectH/core/agent_loop.py#L5054) 의 `_build_web_search_origin`은 `verification_label` 산출에 필터 전 `selected_sources` 대신 필터 후 `role_sources`를 넘기도록 실제로 바뀌었고, [`tests/test_web_app.py`](/home/xpdlqj/code/projectH/tests/test_web_app.py#L9710) 에 `test_handle_chat_latest_update_single_source_verification_label_retained_after_history_card_reload`가 실제로 추가되어 초기 응답, 저장 history, `load_web_search_record_id` reload의 label parity를 잠급니다.
- `/work`의 검증 자기보고도 사실입니다. `python3 -m unittest -v tests.test_web_app`를 다시 돌려 `Ran 127 tests in 2.712s`, `OK`를 확인했고, `git diff --check -- core/agent_loop.py tests/test_web_app.py`도 통과했습니다.
- 범위도 current `projectH` 방향을 벗어나지 않았습니다. 이번 변경은 secondary web investigation의 latest_update badge semantics 보정에 한정되며, approval/reviewed-memory, broad ranking rewrite, browser-visible markup, docs contract 변경은 섞이지 않았습니다.
- docs 무변경도 이번 round-local 범위에서는 truthful합니다. `stat` 기준 [`README.md`](/home/xpdlqj/code/projectH/README.md), [`docs/PRODUCT_SPEC.md`](/home/xpdlqj/code/projectH/docs/PRODUCT_SPEC.md), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md), [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md) mtime은 모두 latest `/work`보다 앞서 있고, 이번 변경도 기존 latest_update badge contract의 truthful fix이지 새 문서 문구를 요구하는 contract 확대가 아니었습니다.
- 추가 대조: 직전 `/verify`가 지적한 single-source noisy reload parity bug는 현재 재현되지 않습니다. 새 regression이 통과했고, same-family manual spot-check에서도 single-source noisy path의 initial/history/reload label drift는 다시 보이지 않았습니다.
- same-family 잔여 리스크도 좁게 다시 확인했습니다. `뉴스 2건 + noisy community 1건` latest_update fixture를 수동 재현하면 initial/history/natural reload/`load_web_search_record_id` reload 모두 `source_roles = ['보조 출처', '보조 기사']`, `verification_label = '다중 출처 참고'`로 일관되며, [`core/source_policy.py`](/home/xpdlqj/code/projectH/core/source_policy.py#L43) 기준 `classify_source_type('https://www.hankyung.com/economy/2025') == 'general'`, `classify_source_type('https://www.mk.co.kr/economy/2025') == 'news'`입니다. 즉 이번 noisy filtering family bug는 닫혔지만, real news-domain coverage 때문에 user-visible badge/source-role이 generic하게 내려가는 인접 개선 여지는 남아 있습니다.
- whole-project audit이 필요한 징후는 없어서 `report/`는 만들지 않았습니다.

## 검증
- `python3 -m unittest -v tests.test_web_app`
  - 통과 (`Ran 127 tests in 2.712s`, `OK`)
- `git diff --check -- core/agent_loop.py tests/test_web_app.py`
  - 통과 (출력 없음)
- 수동 truth 대조
  - `work/3/31/2026-03-31-latest-update-verification-label-reload-parity.md`
  - `verify/3/31/2026-03-31-latest-update-noisy-history-card-reload-lock-verification.md`
  - `.pipeline/codex_feedback.md`
  - `core/agent_loop.py`
  - `tests/test_web_app.py`
  - `README.md`
  - `docs/PRODUCT_SPEC.md`
  - `docs/ACCEPTANCE_CRITERIA.md`
  - `docs/MILESTONES.md`
  - `docs/TASK_BACKLOG.md`
  - `docs/NEXT_STEPS.md`
- 추가 수동 재현
  - `뉴스 2건 + noisy community 1건` latest_update fixture에서 initial/history/natural reload/`load_web_search_record_id` reload의 `response_origin` 비교
  - `classify_source_type('https://www.hankyung.com/economy/2025') -> general`
  - `classify_source_type('https://www.mk.co.kr/economy/2025') -> news`

## 남은 리스크
- latest_update noisy filtering family에서 추적하던 single-source `verification_label` reload drift는 이번 라운드로 truthfully 닫혔습니다.
- 같은 answer-mode 주변의 다음 smallest user-visible improvement는 real news-domain coverage입니다. 현재 `hankyung.com`은 news가 아니라 general로 분류되어, 기사 2건 latest_update도 `보조 출처` / `다중 출처 참고`로 내려갑니다.
- 다음 라운드는 noisy filtering family를 다시 늘리기보다, `hankyung.com` 같은 실제 기사 도메인을 news로 인식시켜 latest_update badge/source-role을 현재 source-policy intent에 맞추는 작은 source-classification slice가 적절합니다.
