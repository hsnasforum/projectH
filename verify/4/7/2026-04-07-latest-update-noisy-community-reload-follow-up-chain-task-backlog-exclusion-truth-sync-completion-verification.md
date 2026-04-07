## 변경 파일
- `verify/4/7/2026-04-07-latest-update-noisy-community-reload-follow-up-chain-task-backlog-exclusion-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `latest-update noisy-community reload follow-up-chain task-backlog exclusion truth-sync completion` 주장이 현재 트리와 docs-only focused verification 범위에서 사실인지 다시 확인하고, 같은 docs truth-sync 축에서 남은 가장 작은 current-risk reduction 한 슬라이스를 다음 Claude 실행 슬롯으로 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. `docs/TASK_BACKLOG.md:85`부터 `docs/TASK_BACKLOG.md:88`까지는 이제 latest-update noisy-community natural-reload + click-reload follow-up/second-follow-up chain contract를 `보조 커뮤니티`, `brunch` negative surface scope와 `기사 교차 확인`, `보조 기사`, `hankyung.com`, `mk.co.kr` positive retention까지 포함해 current truth에 맞게 적고 있습니다.
- latest `/work`가 주장한 docs-only 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/TASK_BACKLOG.md`는 clean이었습니다.
- 따라서 latest-update noisy-community reload follow-up-chain task-backlog exclusion truth-sync는 이번 verification 범위에서 truthful하게 닫혔습니다. `docs/TASK_BACKLOG.md:85`부터 `docs/TASK_BACKLOG.md:88`, `docs/MILESTONES.md:93`, `docs/MILESTONES.md:94`, `README.md:178`부터 `README.md:181`, `docs/ACCEPTANCE_CRITERIA.md:1387`부터 `docs/ACCEPTANCE_CRITERIA.md:1390`, `docs/NEXT_STEPS.md:16`이 같은 truth를 가리킵니다.
- 같은 docs truth-sync 축의 다음 가장 작은 current-risk는 `entity-card noisy single-source claim` reload follow-up chain task-backlog pair입니다. `docs/TASK_BACKLOG.md:89`부터 `docs/TASK_BACKLOG.md:92`까지는 negative claim exclusion과 `source_paths` provenance만 적고 있어, root docs가 적는 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지와 `context box` provenance 표기를 빠뜨립니다.
- 반면 대응 root docs는 이미 더 강한 current truth를 적고 있습니다. `docs/MILESTONES.md:95`, `README.md:182`부터 `README.md:185`, `docs/ACCEPTANCE_CRITERIA.md:1391`부터 `docs/ACCEPTANCE_CRITERIA.md:1394`, `docs/NEXT_STEPS.md:16`은 entity-card noisy single-source claim natural-reload + click-reload follow-up/second-follow-up chain에 대해 `출시일`, `2025`, `blog.example.com` 미노출뿐 아니라 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` 유지와 `blog.example.com` provenance in context box/source_paths를 함께 적습니다.
- 그래서 다음 단일 슬라이스는 `entity-card noisy single-source claim reload follow-up-chain task-backlog provenance truth-sync completion`으로 고정했습니다. 같은 `docs/TASK_BACKLOG.md` 안에서 natural-reload와 click-reload follow-up/second-follow-up 4줄이 동일한 under-spec pattern을 공유하므로, 한 번에 정리하는 편이 micro-slice 반복보다 더 truthful하고 reviewable합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-latest-update-noisy-community-reload-follow-up-chain-task-backlog-exclusion-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-latest-update-natural-reload-task-backlog-response-origin-truth-sync-completion-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '85,92p'`
- `nl -ba docs/MILESTONES.md | sed -n '93,96p'`
- `nl -ba README.md | sed -n '178,185p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1387,1394p'`
- `git diff --check -- docs/TASK_BACKLOG.md`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '39,41p'`
- `nl -ba README.md | sed -n '132,134p'`
- `nl -ba docs/MILESTONES.md | sed -n '50,52p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1341,1343p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n "blog\\.example\\.com|source_paths|context box|설명형 다중 출처 합의|백과 기반|namu\\.wiki|ko\\.wikipedia\\.org" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md docs/MILESTONES.md README.md docs/ACCEPTANCE_CRITERIA.md`

## 남은 리스크
- latest-update noisy-community reload follow-up chain task-backlog family는 이번 verification 범위에서 닫혔습니다. 같은 4줄을 다시 쪼개 검증할 이유는 줄었습니다.
- 다음 docs current-risk는 `docs/TASK_BACKLOG.md:89`부터 `docs/TASK_BACKLOG.md:92`까지의 entity-card noisy single-source claim reload follow-up chain wording under-spec입니다. 현재는 negative claim exclusion과 `source_paths` provenance만 적고 있어, positive retention과 `context box` provenance truth가 root docs보다 약합니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드도 `docs/TASK_BACKLOG.md` 한 파일만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
