# entity-card noisy-single-source docs-next-steps follow-up-second-follow-up exact-negative-anchor truth-sync completion verification

날짜: 2026-04-07

## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-docs-next-steps-follow-up-second-follow-up-exact-negative-anchor-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`는 `docs/NEXT_STEPS.md:16`의 noisy-single-source claim follow-up/second-follow-up chain summary에 root docs가 이미 적고 있는 exact negative assertion을 다시 넣었다고 주장하므로, current tree와 같은 날 최신 `/verify` 기준으로 재대조가 필요했습니다.
- rerun 결과 `docs/NEXT_STEPS.md:16`은 now natural-reload + click-reload follow-up/second-follow-up chain에 `출시일`, `2025`, `blog.example.com` 미노출을 직접 적고 있고, `README.md:182`-`README.md:185`, `docs/MILESTONES.md:95`, `docs/ACCEPTANCE_CRITERIA.md:1391`-`docs/ACCEPTANCE_CRITERIA.md:1394`, `docs/TASK_BACKLOG.md:89`-`docs/TASK_BACKLOG.md:92`가 가리키는 current truth와 맞습니다.
- same-axis 다음 current-risk는 같은 `docs/NEXT_STEPS.md:16`의 crimson-desert exact-field clause가 still `full natural-reload follow-up/second-follow-up chain provenance truth-sync`라고 적혀, follow-up/second-follow-up actual-search clause가 이미 좁혀 둔 current truth보다 강하게 읽힐 수 있다는 점입니다. 이 마지막 판단은 current docs wording에 대한 추론입니다.

## 핵심 변경
- latest `/work`가 truthful함을 확인하고, noisy-single-source chain exact negative-anchor correction이 current truth와 맞음을 persistent `/verify` note로 남겼습니다.
- 다음 Claude 슬라이스를 `entity-card crimson-desert docs-next-steps exact-field chain-provenance overstatement correction`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,240p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `ls -1t verify/4/7 | head -n 8`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-docs-next-steps-follow-up-second-follow-up-exact-negative-anchor-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-crimson-desert-docs-next-steps-follow-up-second-follow-up-provenance-overstatement-correction-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba README.md | sed -n '180,185p'`
- `nl -ba docs/MILESTONES.md | sed -n '94,96p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1394p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,92p'`
- `nl -ba README.md | sed -n '152,165p'`
- `nl -ba docs/MILESTONES.md | sed -n '70,83p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1361,1374p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,72p'`
- `git diff --check -- docs/NEXT_STEPS.md`
- `rg -n "entity-card noisy single-source claim|history-card entity-card noisy single-source claim|entity-card 붉은사막 검색 결과|entity-card 붉은사막 browser natural-reload follow-up/second-follow-up|blog\\.example\\.com|출시일|2025" docs/NEXT_STEPS.md README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md`
- `git status --short`
- docs-only verification round이므로 `python3 -m unittest -v`, Playwright, `make e2e-test`는 재실행하지 않았습니다.

## 남은 리스크
- `docs/NEXT_STEPS.md:16`의 crimson-desert exact-field clause는 still `entity-card 붉은사막 검색 결과 ... blog.example.com provenance in context box, and full natural-reload follow-up/second-follow-up chain provenance truth-sync`라고 적습니다. 반면 대응 root/staged docs인 `README.md:157`-`README.md:165`, `docs/MILESTONES.md:75`-`docs/MILESTONES.md:83`, `docs/ACCEPTANCE_CRITERIA.md:1366`-`docs/ACCEPTANCE_CRITERIA.md:1374`, `docs/TASK_BACKLOG.md:64`-`docs/TASK_BACKLOG.md:72`는 follow-up/second-follow-up actual-search truth를 `namu.wiki`, `ko.wikipedia.org` continuity와 `WEB`/`설명 카드`/`설명형 다중 출처 합의`/`백과 기반` drift prevention으로만 적습니다.
- 따라서 current giant summary는 follow-up/second-follow-up actual-search chain에 `blog.example.com` provenance가 이어진다고 읽힐 여지가 남습니다. 이 리스크는 docs wording 정밀화 수준이며, current shipped behavior 자체가 깨졌다는 뜻은 아닙니다.
