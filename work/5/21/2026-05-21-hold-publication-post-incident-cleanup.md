# 2026-05-21 Hold publication post incident cleanup

## 변경 파일

- `e2e/tests/controller-smoke.spec.mjs`
- `controller/js/cozy.js`
- `.pipeline/archive/2026-05-21/implement_handoff.2084-stale-contained.md`
- `work/5/21/2026-05-21-hold-publication-post-incident-cleanup.md`

## 사용 skill

- `work-log-closeout`: operator 결정, 실제 처리 결과, 검증 및 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/operator_request.md#2072`의 `HOLD_PUBLICATION` 결정에 맞춰 dirty bundle을 local-only로 유지하고, push/PR/merge/release 없이 post-incident cleanup만 수행하기 위함입니다.
- stale `.pipeline/implement_handoff.md#2084`가 재시작 후 다시 dispatch되면서 Codex pane이 범위 밖 변경을 만든 흐름을 차단해야 했습니다.

## 핵심 변경

- 실제 UI 문구와 일치하는 `e2e/tests/controller-smoke.spec.mjs` assertion 2개를 유지하고 로컬 커밋했습니다.
  - 커밋: `d906484 test(e2e): align assertions with Korean UI text`
- 사고성 산출물로 판단한 `controller/js/cozy.js` 변경은 `git restore -- controller/js/cozy.js`로 되돌렸습니다.
- stale active control 재주입을 막기 위해 `.pipeline/implement_handoff.md#2084` 원문을 `.pipeline/archive/2026-05-21/implement_handoff.2084-stale-contained.md`로 이동해 보존했습니다.
- `HOLD_PUBLICATION` 결정은 local-only 유지로 해석했습니다. push, PR, merge, release는 수행하지 않았습니다.

## 검증

- `sed -n '1,220p' .pipeline/operator_request.md`
  - `CONTROL_SEQ: 2072`, `DECISION_REQUIRED`, `HOLD_PUBLICATION` 선택지와 publication boundary를 확인했습니다.
- `sed -n '1,220p' verify/5/21/2026-05-21-post-commit-untracked-triage.md`
  - post-commit untracked triage와 기존 e2e/controller-smoke 맥락을 확인했습니다.
- `rg -n "stale_advisory_pending|대기 중" controller/js/cozy.js controller/js/state.js controller/server.py`
  - 실제 UI가 `대기 중`을 렌더링하는 근거를 확인했습니다.
- `rg -n "Runtime RUNNING|구동 상태 RUNNING|구동 상태|marquee-text" controller/js controller/index.html controller/css`
  - 실제 marquee 문구가 `구동 상태 ${presentation.runtimeState}`임을 확인했습니다.
- `git diff --check -- e2e/tests/controller-smoke.spec.mjs`
  - 통과했습니다.
- `git status --short | awk '!/^\\?\\?/'`
  - e2e 커밋 및 `cozy.js` 복원 후 tracked dirty가 없음을 확인했습니다.

## 남은 리스크

- Playwright는 이 cleanup 라운드에서 새로 실행하지 않았습니다. e2e assertion은 실제 UI 문자열 근거와 맞춰 커밋했지만, browser 실행 검증은 다음 통합 테스트 라운드에서 필요합니다.
- `.pipeline/implement_handoff.md#2084`는 archive 처리했으나, 완료된 handoff를 work/verify artifact 기반으로 중복 탐지하지 못한 구조적 갭은 남아 있습니다.
- 특히 `readme_safety_defaults_memory_boundary_doc_sync`의 `/work` 기록은 있으나 동일 reason의 `/verify` 기록은 확인되지 않았습니다. 다음 구조 개선 후보는 `completed_implement_handoff_truth()`가 work-only 완료 기록이나 verify 누락 상태를 어떻게 fail-closed 처리할지 결정하는 것입니다.
- untracked 파일과 기록 묶음은 여전히 별도 triage 대상입니다.
- commit/push/PR/merge/release 중 publication 계열 작업은 수행하지 않았습니다.
