# 2026-04-22 milestone7 doc cleanup milestone8 entry

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/22/2026-04-22-milestone7-doc-cleanup-milestone8-entry.md`

## 사용 skill
- `doc-sync`: Milestone 문서의 stale keep-later 문구를 현재 shipped 상태에 맞췄다.
- `finalize-lite`: handoff 필수 검증과 문서 변경 범위, closeout 준비 상태를 확인했다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 823
  (`milestone7_doc_cleanup_milestone8_entry`)에 따라 `docs/MILESTONES.md`의
  `edit` 및 scope suggestion field 관련 stale deferral 문구를 제거했다.
- Axis 4 bundle은 이미 SHA `afe0f3a`로 commit/push되었고, Milestone 8 fixture matrix는
  기존 `docs/MILESTONES.md` lines 423-430에 정의되어 있어 새 Milestone 8 내용을
  추가하지 않는 조건을 따랐다.

## 핵심 변경
- Milestone 6 later constraint에서 이미 shipped된 `edit` 언급을 제거했다.
- Milestone 7에 Axis 4 shipped note를 추가해 `suggested_scope` optional free-text field가
  `candidate_review_record` 4-layer 경로에 추가되었음을 기록했다.
- Milestone 7 still-later 목록에서 만족된 "scope suggestion fields later than first
  review-action trace" deferral을 제거했다.
- "Next 3 Implementation Priorities" #2에서 shipped된 `edit`와 basic `suggested_scope`
  field를 later-slice 목록에서 제거하고 shipped 항목으로 옮겼다.
- handoff 제한에 따라 `docs/MILESTONES.md` 외 docs/runtime/e2e/frontend 및 `.pipeline`
  control 파일은 수정하지 않았다.

## 검증
- `git diff --check -- docs/MILESTONES.md` → 통과
- `python3 -m unittest tests.test_smoke -q` → 통과 (`Ran 150 tests`, `OK`)

## 남은 리스크
- minimum scope, conflict, rollback rules와 suggested-scope ordering/justification rule은
  문서상 그대로 reviewed-memory planning 이후 설계 대상으로 남아 있다.
- 작업 전부터 남아 있던 별도 untracked `/work` 파일과 advisory report는 이번 handoff
  범위가 아니어서 건드리지 않았다.
