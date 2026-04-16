# 2026-04-16 reviewed-memory aggregate record-backed lifecycle survives supersession verification

## 변경 파일
- `verify/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-reviewed-memory-aggregate-record-backed-lifecycle-survives-supersession.md`는 seq 206 handoff에서 지적된 회귀를 닫기 위해, pre-emit stale aggregate retire는 유지하면서 record-backed lifecycle aggregate는 supporting correction supersession 뒤에도 계속 보이도록 serializer를 보강했다고 주장합니다.
- 이번 verification 라운드는 그 구현 주장이 현재 tree와 일치하는지 확인하고, `/work`에 직접 적힌 최소 검증 묶음을 다시 돌려 same-family current-risk reduction이 truthfully 닫혔는지 판정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 정적 구현 주장은 현재 tree와 일치합니다.
  - `app/serializers.py`의 `_build_recurrence_aggregate_candidates()`는 `emitted_transition_records`에서 record-backed fingerprint set을 만들고, 해당 fingerprint는 stale check를 건너뜁니다.
  - 같은 함수의 second pass는 main loop에서 사라진 record-backed fingerprint에 대해 stored `aggregate_identity_ref`, `supporting_source_message_refs`, `supporting_candidate_refs`를 써서 synthetic aggregate를 재구성한 뒤 기존 contract / capability / transition-record builder 체인을 다시 적용합니다.
  - `_build_recurrence_aggregate_reviewed_memory_transition_record()`는 stored record가 `emitted_record_only_not_applied`를 지난 경우 capability gate를 우회하고 stored record를 그대로 반환합니다.
  - `tests/test_web_app.py`에는 `test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession`가 존재하고, `e2e/tests/web-smoke.spec.mjs`에는 `same-session recurrence aggregate active lifecycle survives supporting correction supersession` 시나리오가 존재합니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`는 pre-emit retire와 record-backed lifecycle survival을 함께 기술합니다.
- `/work`가 적은 검증 주장은 재실행 결과와도 일치합니다.
  - pre-emit stale retire regression 1건, record-backed lifecycle survival regression 1건, 기존 lifecycle unit 3건은 모두 `OK`였습니다.
  - Playwright의 stale-retire 시나리오와 active-lifecycle-survival 시나리오는 둘 다 통과했습니다.
  - 관련 `git diff --check`는 clean입니다.
- 따라서 latest `/work`는 현재 tree 기준으로 truthful하게 닫혔다고 보는 편이 맞습니다.
  - seq 206에서 지적한 “active effect는 남아 있는데 aggregate card가 사라지는 orphaned control surface” 회귀는 더 이상 재현되지 않았습니다.
  - 이번 라운드가 pre-emit retire semantics까지 깨뜨리지는 않았다는 점도 함께 재확인했습니다.

## 검증
- `rg -n "record-backed|synthetic aggregate|test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession|same-session recurrence aggregate active lifecycle survives supporting correction supersession|current-version only" app/serializers.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 결과: latest `/work`가 주장한 code/test/docs 지점 존재 확인
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidate_retires_on_superseding_correction_before_emit`
  - 결과: `OK (7.492s)`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession`
  - 결과: `OK (7.527s)`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_visible_transition_result_active_effect_lifecycle tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_contract_refs_retained_through_lifecycle tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_boundary_draft_stays_draft_not_applied_through_lifecycle`
  - 결과: `Ran 3 tests in 11.929s` / `OK`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate active lifecycle survives supporting correction supersession" --reporter=line`
  - 결과: `1 passed (39.7s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate stale candidate retires before apply start" --reporter=line`
  - 결과: `1 passed (23.7s)`
- verification note:
  - 첫 Playwright 재실행 시 두 시나리오를 병렬로 띄워 `config.webServer`가 같은 포트에 동시에 bind하려다 `OSError: [Errno 98] Address already in use`가 났습니다.
  - 이는 product regression이 아니라 verification execution collision이어서, 각 시나리오를 순차로 다시 실행해 위 pass 결과를 기준으로 truth를 판정했습니다.
- `git diff --check -- app/serializers.py app/handlers/aggregate.py app/static/app.js tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- full Playwright suite 미실행
  - 이유: 이번 라운드는 serializer-only reviewed-memory regression fix와 관련된 focused unit / focused browser 시나리오만이 직접적인 truth 근거이며, shared browser helper 전반이나 release/ready 판정을 다루는 라운드가 아닙니다.

## 남은 리스크
- current-risk regression은 닫혔지만, aggregate card는 여전히 `supporting_review_refs`나 review-support 상태를 사용자에게 드러내지 않습니다.
- 현재 `app/static/app.js`의 aggregate card는 `반복 N회`, `capability`, `audit`, `family`, `fingerprint`, `계획 타깃`만 보여주고, `reject` / `defer`가 source-message audit-only라 aggregate가 계속 보이는 이유나 accepted review support가 `0건`인지 여부를 visible contract로 설명하지 않습니다.
- 따라서 다음 슬라이스는 same-family user-visible improvement로, review queue `reject` / `defer`와 aggregate trigger가 함께 존재할 때 aggregate support 상태를 visible하게 드러내는 쪽이 맞습니다. 새 quality axis나 docs-only micro-slice보다 우선순위가 높습니다.
