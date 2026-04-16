# 2026-04-16 reviewed-memory aggregate record-backed historical basis clarity verification

## 변경 파일
- `verify/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split-verification.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-reviewed-memory-aggregate-record-backed-historical-basis-clarity.md`는 transition-backed aggregate card에 `[기록된 기준]` inline prefix를 추가해, displayed review-support count가 fresh live support가 아니라 persisted recorded basis를 설명한다는 점을 사용자에게 명시했다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 실제 rerun 결과에 맞는지 확인하고, same-family user-visible clarity slice가 truthful하게 닫혔는지 판정하는 것이 목적입니다.

## 핵심 변경
- 최신 `/work`의 핵심 주장은 현재 tree와 일치합니다.
  - `app/static/app.js`는 `reviewed_memory_transition_record.record_stage`가 비어 있지 않은 aggregate에 대해 `hasRecordedBasis` / `basisPrefix`를 계산하고, 기존 `aggregate-trigger-review-support` 라인 앞에 `[기록된 기준] `을 붙입니다.
  - 같은 파일에서 pre-emit aggregate는 기존 line을 그대로 유지하므로, prefix는 transition-backed aggregate에만 붙습니다.
  - `e2e/tests/web-smoke.spec.mjs`에는 `same-session recurrence aggregate recorded basis label survives supporting correction supersession` 시나리오가 있고, active-effect 진입 직후와 supporting correction supersession + reload 이후 모두 `[기록된 기준]` label 생존을 확인합니다.
  - `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`는 transition-backed aggregate card의 recorded-basis label을 현재 shipped contract로 적고 있습니다.
- latest `/work`가 적은 “`app/serializers.py` 미변경 / `tests/test_web_app.py` 미변경” 설명도 현재 tree와 일치합니다.
  - `git status --short` 기준으로 이번 slice 관련 tracked change는 `app/static/app.js`, `e2e/tests/web-smoke.spec.mjs`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/TASK_BACKLOG.md`에 국한되어 있습니다.
  - `app/serializers.py`와 `tests/test_web_app.py`는 earlier same-day reviewed-memory baseline hunks를 제외하고 이번 slice에서 새 변경이 없습니다.
- `docs/NEXT_STEPS.md`와 `docs/MILESTONES.md`도 다시 확인했습니다.
  - 둘 다 이번 `[기록된 기준]` UI label을 별도로 적지는 않지만, 현재 milestone state나 next-phase ordering과 직접 충돌하는 문장은 보이지 않습니다.
  - 이번 라운드는 새 milestone 진입이나 staged roadmap 이동이 아니라 existing shipped aggregate card copy clarification이므로, 해당 두 문서 미갱신만으로 latest `/work`를 false로 보기는 어렵습니다.
- 따라서 latest `/work`는 현재 tree 기준으로 truthful하게 닫혔다고 보는 편이 맞습니다.
  - 이번 라운드는 payload contract, transition storage, lifecycle semantics를 바꾸지 않았고,
  - transition-backed aggregate card의 visible contract만 더 명시적으로 만들었습니다.

## 검증
- `rg -n "aggregate-trigger-review-support|기록된 기준|reviewed_memory_transition_record|recurrence_count|supporting_review_refs" app/static/app.js`
  - 결과: `[기록된 기준]` prefix와 transition-backed aggregate 판별 로직 존재 확인
- `rg -n "same-session recurrence aggregate recorded basis label survives supporting correction supersession|기록된 기준|aggregate-trigger-review-support" e2e/tests/web-smoke.spec.mjs`
  - 결과: 새 Playwright scenario와 label assertion 지점 존재 확인
- `rg -n "기록된 기준|recorded basis|historical basis" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md docs/MILESTONES.md`
  - 결과: root contract docs 4개에는 새 label wording이 반영되어 있고, `docs/NEXT_STEPS.md` / `docs/MILESTONES.md`에는 이번 label-specific wording이 없지만 현재 단계 설명과 직접 충돌은 확인되지 않음
- `git diff --unified=3 -- app/static/app.js`
  - 결과: `basisPrefix = "[기록된 기준] "`를 기존 review-support line에 붙이는 최소 UI hunk 확인
- `git diff --unified=3 -- e2e/tests/web-smoke.spec.mjs`
  - 결과: transition-backed aggregate + supersession + reload 후 label survival만 검증하는 isolated scenario hunk 확인
- `git diff --unified=3 -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 결과: recorded-basis label docs sync hunk 확인
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_record_backed_lifecycle_survives_supporting_correction_supersession`
  - 결과: `Ran 1 test in 5.692s` / `OK`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate recorded basis label survives supporting correction supersession" --reporter=line`
  - 결과: `1 passed (33.6s)`
- `git diff --check -- app/static/app.js app/serializers.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- full Playwright suite 미실행
  - 이유: 이번 라운드는 transition-backed aggregate card의 inline label wording과 one-scenario browser contract에 한정된 변경이며, shared browser helper 전반이나 release/ready 판정을 다루지 않습니다.

## 남은 리스크
- same-family visible contract는 한 단계 더 명확해졌지만, 이 다음 exact slice는 아직 자동 확정하기 어렵습니다.
- plausible next candidates가 둘 이상 남아 있습니다.
  - same-family refinement: recorded basis label 다음으로, supersession 뒤 current live basis와 persisted recorded basis가 diverge할 때 그 차이를 더 분명히 surface할지
  - axis switch: reviewed-memory visible clarity가 충분히 닫혔다고 보고 다른 shipped `app.web` axis로 넘어갈지
- 현재 `/work`와 `/verify`만으로는 어느 쪽이 더 truthful한 next slice인지 low-confidence라서, 다음 control은 operator stop보다 Gemini arbitration이 더 적절합니다.
