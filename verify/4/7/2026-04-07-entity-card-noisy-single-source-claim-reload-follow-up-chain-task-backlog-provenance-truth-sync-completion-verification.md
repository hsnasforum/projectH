## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-follow-up-chain-task-backlog-provenance-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `entity-card noisy single-source claim reload follow-up-chain task-backlog provenance truth-sync completion` 주장이 현재 트리와 docs-only focused verification 범위에서 사실인지 다시 확인하고, 같은 docs truth-sync 축에서 남은 가장 작은 current-risk reduction 한 슬라이스를 다음 Claude 실행 슬롯으로 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. `docs/TASK_BACKLOG.md:89`부터 `docs/TASK_BACKLOG.md:92`까지는 이제 entity-card noisy single-source claim natural-reload + click-reload follow-up/second-follow-up chain contract를 negative claim exclusion뿐 아니라 `설명형 다중 출처 합의`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org` positive retention과 `source_paths/context box` provenance까지 포함해 current truth에 맞게 적고 있습니다.
- latest `/work`가 주장한 docs-only 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/TASK_BACKLOG.md`는 clean이었습니다.
- 따라서 entity-card noisy single-source claim reload follow-up-chain task-backlog provenance truth-sync는 이번 verification 범위에서 truthful하게 닫혔습니다. `docs/TASK_BACKLOG.md:89`부터 `docs/TASK_BACKLOG.md:92`, `docs/MILESTONES.md:95`, `README.md:182`부터 `README.md:185`, `docs/ACCEPTANCE_CRITERIA.md:1391`부터 `docs/ACCEPTANCE_CRITERIA.md:1394`, `docs/NEXT_STEPS.md:16`이 같은 truth를 가리킵니다.
- 다음 가장 작은 docs truth-sync current-risk는 history-card entity-card actual-search reload family입니다. `docs/TASK_BACKLOG.md:67`부터 `docs/TASK_BACKLOG.md:69`까지는 actual-search source-path plurality와 generic response-origin continuity만 적고 있어, root docs가 적는 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` continuity보다 약합니다.
- 반면 대응 root docs는 이미 더 강한 current truth를 적고 있습니다. `docs/MILESTONES.md:78`부터 `docs/MILESTONES.md:80`, `README.md:160`부터 `README.md:162`, `docs/ACCEPTANCE_CRITERIA.md:1369`부터 `docs/ACCEPTANCE_CRITERIA.md:1371`, `docs/NEXT_STEPS.md:16`은 history-card entity-card actual-search click-reload initial/follow-up/second-follow-up chain에 대해 `namu.wiki`, `ko.wikipedia.org` context box 유지뿐 아니라 `WEB`, `설명 카드`, `설명형 다중 출처 합의`, `백과 기반` response-origin continuity까지 적습니다.
- 그래서 다음 단일 슬라이스는 `history-card entity-card actual-search task-backlog response-origin truth-sync completion`으로 고정했습니다. 같은 `docs/TASK_BACKLOG.md` 안에서 initial/follow-up/second-follow-up 3줄이 동일한 under-spec pattern을 공유하므로, 한 번에 정리하는 편이 micro-slice 반복보다 더 truthful하고 reviewable합니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-follow-up-chain-task-backlog-provenance-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-latest-update-noisy-community-reload-follow-up-chain-task-backlog-exclusion-truth-sync-completion-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `git status --short`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,92p'`
- `nl -ba docs/MILESTONES.md | sed -n '94,96p'`
- `nl -ba README.md | sed -n '182,185p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1394p'`
- `git diff --check -- docs/TASK_BACKLOG.md`
- `rg -n "noisy single-source claim|blog\\.example\\.com|설명형 다중 출처 합의|백과 기반|source_paths/context box|source_paths에|context box에는" docs/TASK_BACKLOG.md docs/MILESTONES.md README.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '67,69p'`
- `nl -ba docs/MILESTONES.md | sed -n '78,80p'`
- `nl -ba README.md | sed -n '160,162p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1369,1371p'`

## 남은 리스크
- entity-card noisy single-source claim reload follow-up-chain task-backlog family는 이번 verification 범위에서 닫혔습니다. 같은 4줄을 다시 쪼개 검증할 이유는 줄었습니다.
- 다음 docs current-risk는 `docs/TASK_BACKLOG.md:67`부터 `docs/TASK_BACKLOG.md:69`까지의 history-card entity-card actual-search wording under-spec입니다. 현재는 source-path plurality와 generic continuity만 적고 있어, explicit response-origin truth가 root docs보다 약합니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드도 `docs/TASK_BACKLOG.md` 한 파일만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
