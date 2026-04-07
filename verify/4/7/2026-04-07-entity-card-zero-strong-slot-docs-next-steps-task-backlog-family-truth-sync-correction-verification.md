## 변경 파일
- `verify/4/7/2026-04-07-entity-card-zero-strong-slot-docs-next-steps-task-backlog-family-truth-sync-correction-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/7/2026-04-07-entity-card-zero-strong-slot-docs-next-steps-task-backlog-family-truth-sync-correction.md`가 docs-only focused verification 범위에서 truthful한지 다시 확인하고, 같은 root-summary/docs truth-sync 축에서 남은 가장 작은 coherent current-risk를 다음 Claude 슬라이스로 고정하기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. `docs/TASK_BACKLOG.md:56`은 entity-card zero-strong-slot click-reload path를 `두 번째 follow-up` 기준으로 바로잡았고, `docs/TASK_BACKLOG.md:57`-`docs/TASK_BACKLOG.md:58`은 natural-reload exact-field/follow-up browser truth를 `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반`, `namu.wiki`, `ko.wikipedia.org`까지 포함해 적고 있습니다.
- `docs/NEXT_STEPS.md:16`도 same family root summary를 current truth에 맞게 반영하고 있었습니다. zero-strong-slot click-reload initial/follow-up/second-follow-up과 natural-reload exact-field/follow-up이 한 family로 읽히고, `namu.wiki`, `ko.wikipedia.org`, `WEB`, `설명 카드`, `설명형 단일 출처`, `백과 기반` continuity가 과장 없이 요약돼 있습니다.
- latest `/work`가 주장한 focused 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`는 clean이었고, 대응 root/staged docs인 `README.md:149`-`README.md:151`, `docs/MILESTONES.md:67`-`docs/MILESTONES.md:69`, `docs/ACCEPTANCE_CRITERIA.md:1358`-`docs/ACCEPTANCE_CRITERIA.md:1360`와 wording도 맞았습니다.
- 따라서 entity-card zero-strong-slot docs-next-steps-task-backlog family truth-sync correction은 이번 verification 범위에서 truthful하게 닫혔습니다.
- 다음 same-axis current-risk는 entity-card 붉은사막 family의 `docs/NEXT_STEPS.md:16` root-summary under-spec입니다. 대응 root/staged docs는 이미 `README.md:152`, `README.md:157`-`README.md:159`, `README.md:165`, `docs/TASK_BACKLOG.md:59`, `docs/TASK_BACKLOG.md:64`-`docs/TASK_BACKLOG.md:66`, `docs/TASK_BACKLOG.md:72`, `docs/MILESTONES.md:70`, `docs/MILESTONES.md:75`-`docs/MILESTONES.md:77`, `docs/MILESTONES.md:83`, `docs/ACCEPTANCE_CRITERIA.md:1361`, `docs/ACCEPTANCE_CRITERIA.md:1366`-`docs/ACCEPTANCE_CRITERIA.md:1368`, `docs/ACCEPTANCE_CRITERIA.md:1374`에서 exact-field noisy exclusion, `namu.wiki`·`ko.wikipedia.org` positive retention, `blog.example.com` provenance, follow-up/second-follow-up response-origin + source-path continuity를 이미 explicit하게 적고 있습니다.
- 반면 `docs/NEXT_STEPS.md:16`의 붉은사막 요약은 exact-field noisy exclusion과 generic한 `full natural-reload follow-up/second-follow-up chain provenance truth-sync`만 적고 있어, root summary에서 same family의 source-path plurality와 second-follow-up closure가 staged docs만큼 직접적으로 읽히지 않습니다. 그래서 다음 단일 슬라이스는 `entity-card crimson-desert docs-next-steps family-closure provenance truth-sync completion`으로 좁혔습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-zero-strong-slot-docs-next-steps-task-backlog-family-truth-sync-correction.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-history-card-entity-card-actual-search-docs-next-steps-family-closure-truth-sync-completion-verification.md`
- `git status --short`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,20p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '54,58p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '56,76p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '59,66p'`
- `nl -ba README.md | sed -n '147,151p'`
- `nl -ba README.md | sed -n '149,166p'`
- `nl -ba docs/MILESTONES.md | sed -n '65,69p'`
- `nl -ba docs/MILESTONES.md | sed -n '65,85p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1356,1360p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1356,1375p'`
- `git diff --check -- docs/NEXT_STEPS.md docs/TASK_BACKLOG.md`
- `rg -n "붉은사막|blog\\.example\\.com|dual-probe|actual-search|zero-strong-slot|noisy single-source claim|noisy-community|latest-update|source_paths|provenance|crimson-desert" docs/NEXT_STEPS.md README.md docs/TASK_BACKLOG.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`
- `rg -n "zero-strong-slot|namu\\.wiki|ko\\.wikipedia\\.org|설명 카드|설명형 단일 출처|백과 기반|follow-up|두 번째 follow-up" docs/NEXT_STEPS.md docs/TASK_BACKLOG.md README.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md`

## 남은 리스크
- entity-card zero-strong-slot family의 docs drift는 이번 verification 범위에서 닫혔지만, `docs/NEXT_STEPS.md:16`의 붉은사막 family root summary는 staged/root docs보다 덜 explicit해서 current truth를 읽는 사람이 `source-path plurality`와 `두 번째 follow-up` closure를 바로 파악하기 어렵습니다.
- 다음 라운드는 `docs/NEXT_STEPS.md` 한 파일에서 붉은사막 family의 exact-field, follow-up, second-follow-up, provenance truth를 root summary wording까지 맞추는 docs-only correction으로 제한하는 편이 안전합니다.
- unrelated dirty worktree가 이미 크므로, 이번에도 범위 밖 파일 정리나 widening은 피해야 합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
