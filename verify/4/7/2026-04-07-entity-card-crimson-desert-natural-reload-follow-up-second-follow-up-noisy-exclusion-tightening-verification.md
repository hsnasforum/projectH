# entity-card crimson-desert natural-reload follow-up/second-follow-up noisy-exclusion tightening verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-tightening-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 crimson-desert natural-reload follow-up/second-follow-up noisy-exclusion browser coverage 2개 추가, scenario count `75`, root docs truth-sync, 그리고 `docs/TASK_BACKLOG.md` 재번호 완료를 주장하므로 실제 browser/service rerun과 docs 대조가 모두 필요했습니다.
- rerun 결과 browser scenarios 추가와 관련 root docs 대부분은 current tree와 맞았습니다. `e2e/tests/web-smoke.spec.mjs:5107`, `e2e/tests/web-smoke.spec.mjs:5185`가 새 noisy-exclusion browser scenarios이고, `README.md:166`, `README.md:167`, `docs/NEXT_STEPS.md:16`, `docs/MILESTONES.md:78`, `docs/MILESTONES.md:79`, `docs/ACCEPTANCE_CRITERIA.md:1369`, `docs/ACCEPTANCE_CRITERIA.md:1370`도 그 truth와 맞습니다.
- 다만 `docs/TASK_BACKLOG.md`는 아직 재번호가 truthful하지 않습니다. `docs/TASK_BACKLOG.md:67`이 `54.`, `docs/TASK_BACKLOG.md:68`이 `57.`, `docs/TASK_BACKLOG.md:69`이 `58.`, `docs/TASK_BACKLOG.md:70`이 다시 `57.`로 이어져 numbering이 단조 증가하지 않고 `55`, `56`이 비어 있습니다. 따라서 latest `/work`의 `TASK_BACKLOG.md ... 56~이후 재번호` 서술은 completion 기준으로는 과장입니다.

## 핵심 변경
- latest `/work`가 behavior/test/대부분의 docs sync 측면에서는 truthful하지만, `docs/TASK_BACKLOG.md` 재번호 completion claim까지 포함하면 부분만 truthful하다고 `/verify`에 기록했습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert natural-reload follow-up-second-follow-up task-backlog renumber truth-sync correction`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `ls -1t verify/4/7 | head -n 12`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-follow-up-second-follow-up-noisy-exclusion-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-exact-field-chain-provenance-overstatement-correction-verification.md`
- `git status --short`
- `rg -n "entity-card 붉은사막 자연어 reload 후.*noisy|scenario count|75 scenarios|56\\. |57\\. |58\\. |59\\. |follow-up noisy|second-follow-up noisy|blog\\.example\\.com|출시일|2025" e2e/tests/web-smoke.spec.mjs README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md tests/test_web_app.py`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4840,5145p'`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '5107,6535p'`
- `nl -ba README.md | sed -n '150,190p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,95p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1360,1395p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '58,95p'`
- `nl -ba tests/test_web_app.py | sed -n '17240,17360p'`
- `rg -n "class WebAppServiceTest|def test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_(follow_up|second_follow_up)" tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTests.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTests.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_follow_up tests.test_web_app.WebAppServiceTest.test_handle_chat_entity_card_noisy_single_source_claim_excluded_after_natural_reload_second_follow_up`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload 후.*noisy" --reporter=line`
- `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- 첫 번째 unittest 명령은 stale class name `WebAppServiceTests` 때문에 `AttributeError`로 실패했고, 실제 클래스명 `WebAppServiceTest`로 바로잡은 rerun은 2개 test 모두 통과했습니다.
- full browser suite나 `make e2e-test`는 재실행하지 않았습니다. shared browser helper 변경이나 release 판정 라운드가 아니라, 새로 추가된 2개 scenario에 대한 isolated rerun으로 충분한 범위였습니다.

## 남은 리스크
- `docs/TASK_BACKLOG.md` numbering이 아직 root docs 중 하나에서만 어긋나 있어 latest `/work` closeout의 completion wording과 current docs truth가 완전히 일치하지 않습니다. 이 mismatch는 user-visible runtime bug는 아니지만, root docs 기준 backlog truth를 읽는 후속 작업자에게는 실제 범위를 혼동시킬 수 있습니다.
- 현재 browser/service coverage 자체는 맞게 잠겼고 `rg -c '^test\\(' e2e/tests/web-smoke.spec.mjs` 결과도 `75`였으므로, 다음 라운드는 `docs/TASK_BACKLOG.md`의 번호만 bounded하게 바로잡는 docs-only correction으로 닫는 편이 가장 작고 reviewable합니다.
