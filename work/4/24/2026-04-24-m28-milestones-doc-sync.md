# 2026-04-24 M28 milestones doc sync

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m28-milestones-doc-sync.md`

## 사용 skill
- `finalize-lite`: handoff 범위가 문서 동기화 1건인지 확인하고 실행 검증과 남은 리스크를 정리했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- M28 Structural Owner Bundle은 Axis 1–2가 완료되었지만 `docs/MILESTONES.md`에는 M28 항목이 없어 문서가 구현 사실보다 뒤처져 있었습니다.
- `Next 3 Implementation Priorities`가 PR #32 merge 대기와 오래된 advisory timeout 상태를 계속 설명하고 있어, 현재 PR #33 / M29 direction / Gemini reliability 상태와 맞지 않았습니다.

## 핵심 변경
- M27 항목 바로 뒤에 `Milestone 28: Structural Owner Bundle` 항목을 추가했습니다.
- M28 guardrail로 write/transition path 한정, `supervisor.py` active_round selection 제외, `.pipeline/state/jobs/` subdirectory isolation already shipped 사실을 기록했습니다.
- Axis 1 `StateMachine.step_verify_close_chain()`과 Axis 2 `StateMachine.release_verify_lease_for_archive()` shipped infrastructure를 구현 사실에 맞춰 적었습니다.
- `Next 3 Implementation Priorities`를 PR #33 merge, M29 direction, Gemini advisory reliability 세 항목으로 교체했습니다.

## 검증
- `sed -n '690,745p' docs/MILESTONES.md`
  - 통과: M27 뒤에 M28 항목이 있고, Next 3가 PR #33 / M29 direction / Gemini reliability로 교체된 것을 확인했습니다.
- `rg -n "Milestone 28|PR #33 merge|M29 direction|Gemini advisory reliability|PR #32 merge" docs/MILESTONES.md`
  - 통과: M28 및 새 Next 3 항목이 존재하고 `PR #32 merge`는 더 이상 매칭되지 않았습니다.
- `git diff --check`
  - 통과: 출력 없음
- `git status --short`
  - 확인: 이번 구현 변경은 `docs/MILESTONES.md`뿐이며, 기존 untracked `work/4/24/2026-04-24-m28-bundle-publish-closeout.md`는 이번 round 시작 전부터 있었습니다.

## 남은 리스크
- M29 방향 자체는 아직 결정하지 않았고, 이번 변경은 문서에 advisory 필요 상태만 기록했습니다.
- `docs/TASK_BACKLOG.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, 소스 코드는 handoff 범위 밖이라 수정하지 않았습니다.
- commit, push, PR 생성/수정 및 `.pipeline/advisory_request.md`, `.pipeline/operator_request.md`는 수행하지 않았습니다.
