# 2026-04-26 M42 deep doc bundle

## 변경 파일
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/4/26/2026-04-26-m42-deep-doc-bundle.md`

참고: 작업 전부터 `docs/MILESTONES.md`는 M41 Axis 2 doc-sync 산출물로 수정 상태였고, 이번 라운드에서 편집하지 않았습니다.

## 사용 skill
- `doc-sync`: M38-M41 구현 truth를 세 핵심 제품 문서에만 반영하고 범위를 넓히지 않았습니다.
- `work-log-closeout`: 실제 변경 파일, 검증 명령, 남은 리스크를 이 closeout으로 정리했습니다.

## 변경 이유
- M38-M41 구현은 완료됐지만 `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`에 신규 E2E wrapper 동작, review queue 메타데이터, preference source-ref 감사 필드, PreferencePanel 표시 계약이 누락되어 있었습니다.
- 세 문서가 현재 shipped truth와 어긋나지 않도록 handoff가 지정한 bounded bundle로 drift를 정리했습니다.

## 핵심 변경
- `e2e/start-server.sh`의 healthcheck 기반 smoke 서버 재사용, isolated mock fallback, `set -e` 하드닝을 제품/아키텍처/acceptance 테스트 게이트에 반영했습니다.
- `review_queue_items`에 `source_session_id`, `source_session_title`, 최대 3개 `context_turns`, `evidence_summary`가 포함되는 현재 payload/패널 계약을 기록했습니다.
- reviewed-candidate preference source refs의 `session_title` / `reason_note` 저장과 `/api/preferences`의 `review_reason_note` / `source_session_title` top-level 노출을 기록했습니다.
- `PreferencePanel`의 `출처 세션` / `결정 사유` audit block 표시를 현재 UI/acceptance 계약으로 반영했습니다.
- `global_candidate_review_recorded`와 `preference_candidate_recorded` task-log action 및 preference-store source-ref 경계를 architecture/acceptance 문서에 맞췄습니다.

## 검증
- `git diff --check -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
  - 통과, 출력 없음.
- `python3 -m unittest -v tests.test_docs_sync`
  - 통과.
  - `Ran 13 tests in 0.029s`
- `git diff --check -- docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md work/4/26/2026-04-26-m42-deep-doc-bundle.md`
  - 통과, 출력 없음.

## 남은 리스크
- 이번 라운드는 문서 drift 정리만 수행했으며 코드, unit/service 기능 테스트, Playwright/E2E는 변경하거나 실행하지 않았습니다.
- `README.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 handoff 범위 밖이라 편집하지 않았습니다.
- 초기 확인 시 이미 있던 `docs/MILESTONES.md`, `verify/4/25/2026-04-25-m36-preference-pause-functional-e2e.md`, `report/gemini/**`, `work/4/25/2026-04-25-m31-bundle-publish-closeout.md`, `work/4/26/2026-04-26-m41-milestones-doc-sync.md`, `verify/4/26/2026-04-26-m41-axis2-milestones-doc-sync.md` 변경/미추적 항목은 이번 범위가 아니라 건드리지 않았습니다.
- 최종 상태에서 `.pipeline/README.md`, `README.md`, `pipeline_runtime/operator_autonomy.py`, `watcher_prompt_assembly.py`, 관련 pipeline runtime test 파일들의 범위 외 수정도 보였지만 이번 handoff 대상이 아니므로 편집하지 않았습니다.
- commit, push, branch/PR 생성, 다음 slice 선택은 수행하지 않았습니다.
