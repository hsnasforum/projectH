# 2026-04-24 docs/MILESTONES priorities doc sync

## 변경 파일
- `docs/MILESTONES.md`

## 사용 skill
- `doc-sync`: stale priority bullets를 현재 shipped truth와 최신 verify 근거에 맞춰 좁게 교체했습니다.
- `finalize-lite`: handoff acceptance에 적힌 `git diff --check`만 실행하고 `/work` closeout을 실제 결과 기준으로 정리했습니다.

## 변경 이유
- `docs/MILESTONES.md`의 `Next 3 Implementation Priorities` 섹션이 `reviewed_memory_boundary_draft`, `future_reviewed_memory_stop_apply`, `future_reviewed_memory_reversal`, `future_reviewed_memory_conflict_visibility` 같은 오래된 planning track 용어를 계속 가리키고 있어 현재 M20–M23 shipped 상태를 오해하게 만들고 있었습니다.
- 최신 verify note (`verify/4/24/2026-04-24-m23-axis1-json-correction-guard.md`, CONTROL_SEQ 99)도 이 stale priorities drift를 현재 open risk로 명시하고 있어, 이번 라운드는 그 문서 drift만 좁게 제거하는 doc-sync slice입니다.

## 핵심 변경
- `docs/MILESTONES.md`의 `## Next 3 Implementation Priorities` 아래 3개 bullet을 현재 사실 기반 항목으로 교체했습니다.
  - global candidate E2E test isolation
  - PR #32 merge pending
  - next milestone direction should be chosen via advisory
- handoff 경계에 따라 milestone entries(M13–M23), code files, 다른 문서들은 건드리지 않았습니다.
- stale `reviewed_memory_boundary_draft` / `future_reviewed_memory_*` priority references는 해당 섹션에서 제거했습니다.

## 검증
- `git diff --check -- docs/MILESTONES.md`
  - 통과: 출력 없음
- `rg -n "reviewed_memory_boundary_draft|future_reviewed_memory_stop_apply|future_reviewed_memory_reversal|future_reviewed_memory_conflict_visibility" docs/MILESTONES.md`
  - 확인: stale priority references는 `## Next 3 Implementation Priorities` 섹션에서 제거됐습니다.
  - 다만 동일 문자열이 문서의 기존 shipped history / open question 구간에는 여전히 남아 있습니다. handoff 경계가 "우선순위 섹션만 교체"였기 때문에 해당 historical 서술은 이번 라운드에서 수정하지 않았습니다.

## 남은 리스크
- 이번 라운드는 doc-sync-only 범위라서 코드나 테스트를 재실행하지 않았습니다. 문서가 현재 truth를 더 정확히 반영하게 된 것이지, 새로운 기능이나 검증이 추가된 것은 아닙니다.
- `PR #32` merge pending, global candidate test isolation 부재, next milestone direction 미정은 문서에 반영된 현재 open item이며 이번 implement round에서 해결하지는 않았습니다.
- `docs/MILESTONES.md`의 older shipped-history / `OPEN QUESTION` 구간에는 `reviewed_memory_boundary_draft`, `future_reviewed_memory_*` 문자열이 여전히 남아 있습니다. 이번 handoff는 `Next 3 Implementation Priorities`만 교체하도록 제한되어 있었으므로, 그 wider doc cleanup은 별도 doc-sync slice가 필요합니다.
- 작업 시작 시점에 이미 존재하던 unrelated dirty/untracked 상태(`pipeline_runtime/operator_autonomy.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `watcher_prompt_assembly.py`, 일부 `report/gemini/*`, `work/4/23/*`)는 건드리지 않았습니다.
