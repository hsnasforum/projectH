## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-docs-next-steps-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `entity-card noisy single-source claim docs-next-steps truth-sync completion` 주장이 현재 트리와 docs-only focused verification 결과에 맞는지 다시 확인하고, same-family에서 실제로 남은 마지막 root-doc mismatch를 한 슬라이스로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`가 말한 changed-file 범위는 현재 트리와 일치했습니다. [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)에는 더 이상 entity-card click reload를 generic `설명형 단일 출처` retention으로만 적지 않고, history-card noisy single-source claim exclusion에 `설명형 다중 출처 합의`, `출시일` / `2025` / `blog.example.com` 본문·origin detail 미노출, `blog.example.com` provenance in context box를 함께 적고 있습니다. entity-card 붉은사막 natural-reload initial path도 noisy exclusion + provenance wording으로 바뀌었습니다.
- docs-only verification 범위 자체도 통과했습니다. `rg`로 `docs/NEXT_STEPS.md` 안의 `설명형 다중 출처 합의`, `출시일`, `2025`, `blog.example.com` 반영을 다시 확인했고, `git diff --check -- docs/NEXT_STEPS.md`도 clean이었습니다.
- 다만 latest `/work`의 closeout 문구는 여전히 과장입니다. later docs인 [`README.md`](/home/xpdlqj/code/projectH/README.md#L182), [`README.md`](/home/xpdlqj/code/projectH/README.md#L185), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1391), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1394), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L95), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L89)부터 [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L92)까지는 noisy single-source claim family를 natural-reload + click-reload follow-up/second-follow-up provenance truth-sync로 explicit하게 닫고 있습니다.
- 반대로 root summary인 [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 아직 initial-path 중심 서술에 머물러 있습니다. history-card noisy single-source claim initial click-reload와 entity-card 붉은사막 initial natural-reload는 now truthful하게 들어갔지만, same-family follow-up / second-follow-up provenance truth-sync closure는 root summary에 explicit하게 반영되지 않았습니다. 따라서 latest `/work`의 “initial/follow-up/second-follow-up, natural-reload/click-reload 전체 경로가 service/browser/docs 모두에서 provenance truth-sync 완료” 문구는 `docs/NEXT_STEPS.md` 기준으로는 아직 과장입니다.
- 그래서 현재 truthful closure는 `docs/NEXT_STEPS.md`의 initial-path truth-sync까지로 정리했고, 다음 단일 슬라이스는 `entity-card noisy single-source claim docs-next-steps family-closure truth-sync tightening`으로 고정했습니다. 목표는 `docs/NEXT_STEPS.md:16` 한 곳에서 same-family follow-up / second-follow-up noisy provenance closure까지 later docs와 같은 수준으로 요약하거나, 최소한 initial-path-only처럼 오해될 generic wording을 제거해 root summary도 family closure truth를 따라가게 하는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-docs-next-steps-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-natural-reload-exact-field-provenance-truth-sync-completion-verification.md`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `rg -n "설명형 단일 출처|설명형 다중 출처 합의|blog\\.example\\.com|출시일|2025|history-card entity-card|entity-card noisy single-source claim|entity-card 붉은사막 검색 결과 browser natural-reload exact-field smoke" docs/NEXT_STEPS.md`
- `git diff --check -- docs/NEXT_STEPS.md`
- `sed -n '1,220p' .pipeline/claude_handoff.md`
- `rg -n "follow-up|second-follow-up|blog\\.example\\.com|noisy single-source claim|붉은사막 browser natural-reload follow-up|history-card entity-card" docs/NEXT_STEPS.md`
- `nl -ba README.md | sed -n '180,186p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1390,1395p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '88,92p'`
- `nl -ba docs/MILESTONES.md | sed -n '93,96p'`

## 남은 리스크
- latest `/work`의 changed-file와 docs-only verification 범위는 truthful했지만, closeout의 family-complete 문구는 `docs/NEXT_STEPS.md` root summary 기준으로는 아직 과장입니다.
- `docs/NEXT_STEPS.md`가 initial-path 중심 wording에 머물면 이후 handoff가 noisy single-source claim follow-up/second-follow-up provenance family를 다시 미완료로 읽거나, 반대로 이미 닫힌 later docs와 불필요하게 어긋날 수 있습니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 `docs/NEXT_STEPS.md` 한 파일만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 docs-only 범위였으므로 `unittest`, Playwright, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
