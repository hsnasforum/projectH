# entity-card crimson-desert docs-next-steps follow-up-second-follow-up provenance-overstatement correction verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-follow-up-second-follow-up-provenance-overstatement-correction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `docs/NEXT_STEPS.md:16`의 crimson-desert actual-search follow-up/second-follow-up giant-summary overstatement를 보정했다고 주장하므로, root docs와 browser/service truth에 맞게 실제로 좁혀졌는지 다시 확인해야 했습니다.
- rerun 결과 `docs/NEXT_STEPS.md:16`의 `entity-card 붉은사막 browser natural-reload follow-up/second-follow-up` clause는 이제 `blog.example.com` provenance를 제거했고, `README.md:157`, `README.md:159`, `README.md:165`, `docs/MILESTONES.md:75`, `docs/MILESTONES.md:77`, `docs/MILESTONES.md:83`, `docs/ACCEPTANCE_CRITERIA.md:1366`, `docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/ACCEPTANCE_CRITERIA.md:1374`, `docs/TASK_BACKLOG.md:64`, `docs/TASK_BACKLOG.md:66`, `docs/TASK_BACKLOG.md:72`, `e2e/tests/web-smoke.spec.mjs:4870`, `e2e/tests/web-smoke.spec.mjs:5045`, `tests/test_web_app.py:16443`, `tests/test_web_app.py:16582`가 가리키는 actual-search family truth와 일치했습니다.
- same-family 다음 current-risk는 같은 `docs/NEXT_STEPS.md:16` 안의 noisy-single-source claim follow-up/second-follow-up chain summary가 root docs보다 약하게 적혀 있다는 점입니다.

## 핵심 변경
- latest `/work`가 truthful함을 확인하고, crimson-desert follow-up/second-follow-up actual-search clause의 provenance-overstatement correction이 current truth와 맞음을 persistent `/verify` note로 남겼습니다.
- 다음 Claude 슬라이스를 `entity-card noisy-single-source docs-next-steps follow-up-second-follow-up exact-negative-anchor truth-sync completion`으로 고정했습니다.

## 검증
- `sed -n '1,240p' work/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-follow-up-second-follow-up-provenance-overstatement-correction.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-natural-reload-exact-field-milestones-acceptance-provenance-plurality-truth-sync-completion-verification.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba README.md | sed -n '182,185p'`
- `nl -ba docs/MILESTONES.md | sed -n '94,96p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1394p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,92p'`
- `git diff --check -- docs/NEXT_STEPS.md`
- `git diff --check -- verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-follow-up-second-follow-up-provenance-overstatement-correction-verification.md .pipeline/claude_handoff.md`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/NEXT_STEPS.md:16`의 noisy-single-source claim chain summary는 `README.md:182`, `README.md:183`, `README.md:184`, `README.md:185`, `docs/MILESTONES.md:95`, `docs/ACCEPTANCE_CRITERIA.md:1391`, `docs/ACCEPTANCE_CRITERIA.md:1392`, `docs/ACCEPTANCE_CRITERIA.md:1393`, `docs/ACCEPTANCE_CRITERIA.md:1394`, `docs/TASK_BACKLOG.md:89`, `docs/TASK_BACKLOG.md:90`, `docs/TASK_BACKLOG.md:91`, `docs/TASK_BACKLOG.md:92`가 명시하는 follow-up/second-follow-up exact negative assertion을 giant summary에서 직접 다시 적지 않습니다. current truth는 chain 전체에서 본문/origin detail에 `출시일`, `2025`, `blog.example.com` 미노출을 유지하면서 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` retention과 `blog.example.com` provenance를 함께 적는 것입니다.
