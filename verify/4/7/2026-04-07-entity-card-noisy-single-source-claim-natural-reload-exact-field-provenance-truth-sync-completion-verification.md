## 변경 파일
- `verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-natural-reload-exact-field-provenance-truth-sync-completion-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`의 `entity-card noisy single-source claim natural-reload exact-field provenance truth-sync completion` 주장이 현재 트리와 focused rerun 결과에 맞는지 다시 확인하고, same-family에서 실제로 남은 마지막 contract mismatch를 한 슬라이스로 좁혀 다음 Claude 실행 슬롯에 넘기기 위해서입니다.

## 핵심 변경
- 최신 `/work`가 적은 구현 파일 범위는 현재 트리와 일치했습니다. [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4242)와 [`e2e/tests/web-smoke.spec.mjs`](/home/xpdlqj/code/projectH/e2e/tests/web-smoke.spec.mjs#L4314)는 모두 noisy 3-source fixture로 바뀌었고, scenario 40은 `출시일` / `2025` / `blog.example.com`의 본문·origin detail 미노출, `확인된 사실:` / `교차 확인` 유지, `#context-box`의 `blog.example.com` provenance까지 확인합니다. scenario 46도 `설명형 다중 출처 합의` fixture와 `blog.example.com` provenance를 확인하도록 현재 truth에 맞춰졌습니다.
- 최신 `/work`가 적은 docs truth-sync도 변경된 파일 범위 안에서는 일치했습니다. [`README.md`](/home/xpdlqj/code/projectH/README.md#L152) [`README.md`](/home/xpdlqj/code/projectH/README.md#L158), [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1361) [`docs/ACCEPTANCE_CRITERIA.md`](/home/xpdlqj/code/projectH/docs/ACCEPTANCE_CRITERIA.md#L1367), [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L70) [`docs/MILESTONES.md`](/home/xpdlqj/code/projectH/docs/MILESTONES.md#L76), [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L59) [`docs/TASK_BACKLOG.md`](/home/xpdlqj/code/projectH/docs/TASK_BACKLOG.md#L65)은 natural-reload exact-path noisy provenance truth를 반영합니다.
- focused rerun 결과도 최신 `/work`의 검증 범위 자체는 통과했습니다. Playwright scenario 40, 46이 모두 통과했고, 대상 파일 `git diff --check`도 clean이었습니다. 이번 라운드는 browser/docs-only 변경이라 `unittest`와 전체 browser suite는 재실행하지 않았습니다.
- 다만 latest `/work`의 family closure 주장은 아직 과장입니다. root-doc snapshot인 [`docs/NEXT_STEPS.md`](/home/xpdlqj/code/projectH/docs/NEXT_STEPS.md#L16)은 여전히 entity-card click reload를 `설명형 단일 출처` generic retention으로 요약하고, entity-card 붉은사막 natural-reload도 noisy provenance truth가 아닌 generic smoke 수준으로만 서술합니다. `blog.example.com` provenance와 initial/follow-up family closure가 이 문서에 반영되지 않았습니다.
- 따라서 현재 truthful closure는 `tests + README/ACCEPTANCE/MILESTONES/TASK_BACKLOG`까지이고, next exact slice는 `entity-card noisy single-source claim docs-next-steps truth-sync completion`으로 고정했습니다. 목표는 `docs/NEXT_STEPS.md`의 browser coverage snapshot을 current truth에 맞게 고쳐, same-family click-reload / natural-reload / follow-up / second-follow-up noisy provenance contract가 이미 닫혔다는 점을 문서 한 곳에서도 과장이나 누락 없이 맞추는 것입니다.

## 검증
- `git status --short`
- `sed -n '1,260p' work/4/7/2026-04-07-entity-card-noisy-single-source-claim-natural-reload-exact-field-provenance-truth-sync-completion.md`
- `sed -n '1,260p' verify/4/7/2026-04-07-entity-card-noisy-single-source-claim-reload-exact-field-provenance-truth-sync-tightening-verification.md`
- `sed -n '1,220p' AGENTS.md`
- `sed -n '1,220p' work/README.md`
- `sed -n '1,220p' verify/README.md`
- `sed -n '1,220p' .pipeline/README.md`
- `sed -n '1,220p' .agents/skills/round-handoff/SKILL.md`
- `rg -n "entity-card 붉은사막 검색 결과 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다|entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다|blog\\.example\\.com|설명형 단일 출처|설명형 다중 출처 합의" e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
- `nl -ba e2e/tests/web-smoke.spec.mjs | sed -n '4240,4475p'`
- `nl -ba README.md | sed -n '148,160p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1358,1369p'`
- `nl -ba docs/MILESTONES.md | sed -n '68,78p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '56,66p'`
- `nl -ba docs/NEXT_STEPS.md | sed -n '14,18p'`
- `nl -ba README.md | sed -n '176,190p'`
- `nl -ba docs/ACCEPTANCE_CRITERIA.md | sed -n '1388,1404p'`
- `nl -ba docs/MILESTONES.md | sed -n '90,98p'`
- `nl -ba docs/TASK_BACKLOG.md | sed -n '86,94p'`
- `rg -n "설명형 단일 출처|entity-card 붉은사막 검색 결과 browser natural-reload exact-field smoke|blog\\.example\\.com" docs/NEXT_STEPS.md`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 검색 결과 자연어 reload에서 response origin badge와 answer-mode badge가 유지됩니다" --reporter=line`
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "entity-card 붉은사막 자연어 reload에서 source path가 context box에 유지됩니다" --reporter=line`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 최신 `/work`의 changed-file 범위는 truthful했지만, `docs/NEXT_STEPS.md`가 still stale이라 same-family closure를 완전히 닫았다고 보기 어렵습니다.
- root-doc snapshot이 generic wording을 유지하면 이후 handoff가 다시 이미 닫힌 noisy provenance family를 미완료로 오판할 수 있습니다.
- unrelated dirty worktree가 이미 크므로, 다음 구현 라운드는 `docs/NEXT_STEPS.md`만 좁게 건드리는 편이 안전합니다.
- 이번 focused verification은 browser/docs-only 범위였으므로 `unittest`, `make e2e-test`, 전체 Python 회귀는 재실행하지 않았습니다.
