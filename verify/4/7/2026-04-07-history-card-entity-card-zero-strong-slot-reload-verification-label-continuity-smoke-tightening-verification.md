## 변경 파일
- `verify/4/7/2026-04-07-history-card-entity-card-zero-strong-slot-reload-verification-label-continuity-smoke-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/7/2026-04-07-history-card-entity-card-zero-strong-slot-reload-verification-label-continuity-smoke-tightening.md`가 current tree 기준으로 truthful한지 다시 확인해야 했습니다.
- same-day latest `/verify`가 직전 news-only follow-up source-path continuity 라운드(`verify/4/7/2026-04-07-history-card-latest-update-news-only-follow-up-source-path-continuity-tightening-verification.md`)를 가리키고 있어, 이번 zero-strong-slot reload verification-label continuity 라운드 기준의 검증 truth와 다음 exact slice를 다시 고정할 필요가 있었습니다.

## 핵심 변경
- latest `/work`의 새 Playwright scenario 추가, scenario count `35`, focused rerun 주장은 current tree와 일치합니다. `e2e/tests/web-smoke.spec.mjs:3148`에는 zero-strong-slot entity-card reload scenario가 실제로 들어 있고, 기존 service 회귀 `tests/test_web_app.py:9047-9111`도 그대로 존재합니다. 문서 count도 `README.md:147`, `docs/ACCEPTANCE_CRITERIA.md:1356`, `docs/MILESTONES.md:65`, `docs/TASK_BACKLOG.md:54`, `docs/NEXT_STEPS.md:16`에서 scenario 35 기준으로 맞춰져 있었고, `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l` 결과도 실제로 `35`였습니다. `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`도 clean이었습니다.
- 좁은 재실행도 다시 통과했습니다. `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields`는 `OK (0.036s)`, `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card zero-strong-slot 다시 불러오기 후 downgraded verification badge와 verification label이 유지됩니다" --reporter=line`은 `1 passed (6.3s)`였습니다.
- 다만 이번 라운드는 완전히 닫히지 않았습니다. 새 smoke가 실제로 확인하는 것은 `#response-origin-badge`의 `WEB`, `#response-answer-mode-badge`의 `설명 카드`, 그리고 `#response-origin-detail`의 `설명형 단일 출처` / `백과 기반`입니다(`e2e/tests/web-smoke.spec.mjs:3222-3234`). 그런데 scenario title 자체가 `downgraded verification badge`를 말하고 있고(`e2e/tests/web-smoke.spec.mjs:3148`), `README.md:147`도 `설명 카드`를 verification badge처럼 설명해 현재 구현과 용어가 어긋납니다. `설명 카드`는 response answer-mode badge이지 verification-strength badge가 아닙니다. 반면 `docs/ACCEPTANCE_CRITERIA.md:1356`, `docs/MILESTONES.md:65`, `docs/TASK_BACKLOG.md:54`는 verification label / source role continuity로 적혀 있어 current behavior와 맞습니다. 따라서 latest `/work`는 smoke 추가와 rerun 자체는 truthful하지만, README와 scenario naming의 truth-sync가 비어 있어 완전히 truthful하게 닫히지는 않았습니다.
- 다음 exact slice는 `history-card entity-card zero-strong-slot reload answer-mode wording sync`로 고정했습니다. 이유는 새 browser contract를 더 넓히기 전에, current shipped docs와 scenario naming에서 `설명 카드`를 verification badge처럼 오해시키는 현재 mismatch를 먼저 바로잡아야 하기 때문입니다. 이 판단은 current tree와 latest `/work`의 문구 차이를 기준으로 한 추론입니다.

## 검증
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-entity-card-zero-strong-slot-reload-verification-label-continuity-smoke-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-latest-update-news-only-follow-up-source-path-continuity-tightening-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `ls -lt work/4/7 verify/4/7 | sed -n '1,120p'`
- `rg -n "history-card entity-card zero-strong-slot 다시 불러오기 후 downgraded verification badge와 verification label이 유지됩니다|35 browser scenarios|scenario 35|zero-strong-slot reload verification-label continuity|검증 중|설명형 단일 출처|백과 기반" e2e/tests/web-smoke.spec.mjs tests/test_web_app.py README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '3140,3255p'`
- `nl -ba tests/test_web_app.py | sed -n '9040,9120p'`
- `rg -n '^test\(' e2e/tests/web-smoke.spec.mjs | wc -l`
  - `35`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - clean
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_zero_strong_slot_entity_card_history_card_reload_exact_fields`
  - `OK (0.036s)`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "history-card entity-card zero-strong-slot 다시 불러오기 후 downgraded verification badge와 verification label이 유지됩니다" --reporter=line`
  - `1 passed (6.3s)`
- `nl -ba README.md | sed -n '144,149p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1354,1358p'`
- `nl -ba docs/MILESTONES.md | sed -n '63,66p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '53,55p'`
- `rg -n "verification badge\\(|downgraded verification badge|설명 카드\\)|검증 중.*설명형 단일 출처|answer-mode badge" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md work/4/7/2026-04-07-history-card-entity-card-zero-strong-slot-reload-verification-label-continuity-smoke-tightening.md`
- `nl -ba tests/test_web_app.py | sed -n '14836,14936p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '1332,1448p'`
- `rg -n "zero-strong.*follow|follow_up.*zero|zero-strong-slot.*load_web_search_record_id \\+ user_text|zero-strong-slot.*follow-up|downgraded.*follow-up|zero strong.*follow" tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- latest `/work`의 smoke 추가와 focused rerun 자체는 맞지만, `README.md:147`와 `e2e/tests/web-smoke.spec.mjs:3148`가 `설명 카드`를 verification badge처럼 적고 있어 current implementation wording과 어긋납니다.
- current tree에는 generic entity-card follow-up continuity(`tests/test_web_app.py:14840-14932`, `e2e/tests/web-smoke.spec.mjs:1332-1447`)는 있지만, zero-strong-slot variant를 별도로 지목한 follow-up contract는 아직 없습니다. 다만 이번 라운드에서는 truth-sync mismatch가 먼저입니다.
- `make e2e-test`와 전체 Python 회귀는 이번 verification에서 재실행하지 않았습니다. 이번 라운드는 single-test + single-scenario 범위였고, shared browser helper나 runtime helper 변경도 없었습니다.
