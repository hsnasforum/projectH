## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-initial-click-reload-milestones-backlog-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `entity-card noisy single-source claim initial click-reload milestones-backlog truth-sync completion` 주장이 현재 트리와 docs-only focused verification 결과에 맞는지 다시 확인하고, 같은 staged-doc truth-sync 축에서 남은 가장 작은 current-risk reduction 슬라이스를 하나로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`의 changed-file 범위는 현재 트리와 일치했습니다. [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L52)와 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L41)은 now history-card entity-card noisy single-source claim initial click-reload contract를 `설명형 다중 출처 합의`, `백과 기반`, negative `출시일` / `2025` / `blog.example.com`, agreement-backed fact card retention, `blog.example.com` provenance in context box/source_paths까지 포함해 current truth에 맞게 적고 있습니다.
- latest `/work`가 주장한 docs-only 검증 핵심도 현재 트리에서 재현됐습니다. `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean이었습니다.
- 이번 라운드 기준으로 entity-card noisy single-source claim family의 root-doc truth-sync는 truthful하게 닫혔습니다. initial click-reload contract는 [`README.md`](/home/xpdlqj/code/projectH/README.md#L134), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1343), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L52), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L41)에 맞춰졌고, follow-up/second-follow-up chain과 root summary도 [`README.md`](/home/xpdlqj/code/projectH/README.md#L182), [`README.md`](/home/xpdlqj/code/projectH/README.md#L185), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1391), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1394), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L95), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L89), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L92), [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)에서 current truth와 맞아 있습니다.
- 따라서 latest `/work`의 family-complete 서술은 이번 verification 범위에서 truthful했습니다. 다음 가장 작은 docs truth-sync current-risk는 adjacent initial click-reload backlog pair로 옮겨집니다. [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L53)와 [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L54), [`README.md`](/home/xpdlqj/code/projectH/README.md#L135), [`README.md`](/home/xpdlqj/code/projectH/README.md#L136), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1344), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1345)는 history-card entity-card dual-probe와 latest-update mixed-source initial click-reload contract를 source path뿐 아니라 `WEB`/answer-mode/verification/source-role retention까지 적습니다.
- 반면 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L42)와 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L43)은 아직 source-path continuity만 적고 response-origin continuity를 빠뜨립니다. 그래서 다음 단일 슬라이스는 `history-card dual-probe mixed-source initial click-reload task-backlog response-origin truth-sync completion`으로 고정했습니다.

## 검증
- `git status --short`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-initial-click-reload-milestones-backlog-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-latest-update-noisy-community-initial-click-reload-staged-doc-truth-sync-completion-verification.md`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/MILESTONES.md | sed -n '51,53p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '40,42p'`
- `nl -ba README.md | sed -n '134,135p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1342,1344p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `nl -ba docs/MILESTONES.md | sed -n '93,96p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '89,92p'`
- `nl -ba README.md | sed -n '182,185p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1391,1394p'`
- `nl -ba docs/MILESTONES.md | sed -n '47,55p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '37,45p'`
- `nl -ba README.md | sed -n '134,143p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1343,1352p'`
- `rg -n 'entity-card noisy single-source claim|출시일|2025|blog\\.example\\.com|설명형 다중 출처 합의|백과 기반|agreement-backed|source_paths|context box' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `rg -n 'dual-probe source-path|mixed-source source-path|response-origin continuity|WEB badge|설명 카드|공식\\+기사 교차 확인|보조 기사|공식 기반|store\\.steampowered\\.com|yna\\.co\\.kr|pearlabyss\\.com/200|pearlabyss\\.com/300' README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `git diff --check -- docs/MILESTONES.md docs/TASK_BACKLOG.md`

## 남은 리스크
- entity-card noisy single-source claim docs family는 이번 verification 범위에서 root docs 기준으로 닫혔습니다. 따라서 같은 family를 더 micro-slice로 쪼갤 이유는 줄었습니다.
- 다음 docs current-risk는 initial click-reload backlog pair의 response-origin under-spec입니다. `docs/TASK_BACKLOG.md:42`와 `docs/TASK_BACKLOG.md:43`이 current shipped contract보다 약하게 적고 있습니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 `docs/TASK_BACKLOG.md` 한 파일만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
