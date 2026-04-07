## 변경 파일
- `verify/4/7/2026-04-07-history-card-noisy-single-source-docs-next-steps-click-reload-exact-field-provenance-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/7/2026-04-07-history-card-noisy-single-source-docs-next-steps-click-reload-exact-field-provenance-truth-sync-completion.md`가 현재 트리와 cross-doc truth에 맞는지 다시 확인하고, same-family current-risk를 다음 Claude 슬라이스 하나로 고정하기 위해서입니다.

## 핵심 변경
- latest `/work`의 changed-file 범위 자체는 현재 트리와 일치했습니다. `docs/NEXT_STEPS.md:16`의 `history-card entity-card 다시 불러오기 noisy single-source claim exclusion` clause는 now `설명형 다중 출처 합의`, `백과 기반`, negative assertions for `출시일` / `2025` / `blog.example.com`, positive agreement-backed fact card retention, `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance를 직접 적고 있습니다.
- 다만 latest `/work`의 completion 서술은 이번 재대조 범위에서 fully truthful하지 않았습니다. same-family cross-doc truth가 아직 닫히지 않았기 때문입니다. `README.md:134`와 `docs/NEXT_STEPS.md:16`, 그리고 `tests/test_web_app.py`의 noisy single-source click-reload assertions는 `namu.wiki`, `ko.wikipedia.org`, `blog.example.com` provenance를 가리키지만, `docs/MILESTONES.md:52`, `docs/ACCEPTANCE_CRITERIA.md:1343`, `docs/TASK_BACKLOG.md:41`는 아직 `blog.example.com` provenance만 직접 적고 있어 exact-field docs truth가 서로 다릅니다.
- 따라서 이번 라운드 기준 latest `/work`는 "`docs/NEXT_STEPS.md` 한 줄 correction은 반영됨"까지는 truthful하지만, 파일명과 본문이 말한 `... truth-sync completion`까지 닫혔다고 보기는 어렵습니다.
- 남은 same-family smallest current-risk는 stale docs trio correction입니다. 다음 단일 슬라이스를 `history-card noisy-single-source initial-click-reload milestones-acceptance-task-backlog provenance truth-sync completion`으로 고정했습니다.

## 검증
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,260p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-history-card-noisy-single-source-docs-next-steps-click-reload-exact-field-provenance-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-docs-next-steps-natural-reload-exact-field-truth-sync-completion-verification.md`
- `git status --short`
- `sed -n '1,260p' .pipeline/claude_handoff.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '1,80p'`
- `nl -ba README.md | sed -n '130,160p'`
- `nl -ba README.md | sed -n '158,176p'`
- `nl -ba docs/MILESTONES.md | sed -n '48,80p'`
- `nl -ba docs/MILESTONES.md | sed -n '76,92p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1340,1370p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1366,1382p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '38,70p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '66,74p'`
- `sed -n '1,220p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-exact-field-provenance-truth-sync-tightening.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-exact-field-provenance-truth-sync-tightening-verification.md`
- `sed -n '1,220p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-initial-click-reload-milestones-backlog-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-initial-click-reload-milestones-backlog-truth-sync-completion-verification.md`
- `git diff --check -- docs/NEXT_STEPS.md`
- `nl -ba docs/MILESTONES.md | sed -n '52,52p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1343,1343p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '41,41p'`
- `nl -ba README.md | sed -n '134,134p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '16,16p'`
- `rg -n "namu\\.wiki|ko\\.wikipedia\\.org|blog\\.example\\.com|설명형 다중 출처 합의|백과 기반|agreement-backed fact card|출시일|2025" README.md docs/NEXT_STEPS.md docs/MILESTONES.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md tests/test_web_app.py`
- docs-only verification 라운드이므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.

## 남은 리스크
- `docs/MILESTONES.md:52`, `docs/ACCEPTANCE_CRITERIA.md:1343`, `docs/TASK_BACKLOG.md:41`는 current noisy single-source click-reload exact-field truth보다 여전히 약합니다. 이 상태로 두면 `/work`와 `/verify`가 다시 same-family completion을 과장할 위험이 큽니다.
- 최신 `/work`의 changed-file 범위는 `docs/NEXT_STEPS.md` 한 파일이어서, 같은 family correction이 아직 root/staged docs 전체에 닫히지 않았습니다.
- unrelated dirty worktree가 이미 크므로, 다음 라운드도 관련 docs 3개만 좁게 수정하는 편이 안전합니다.
