STATUS: verified
CONTROL_SEQ: 1491
BASED_ON_WORK:
  - work/4/30/2026-04-30-controller-lane-state-truth.md
  - work/4/30/2026-04-30-pipeline-runtime-resume-guard.md
  - work/4/30/2026-04-30-m110-review-queue-search-filter.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1491

---

# 2026-04-30 controller/runtime 인프라 수정 + M110 Axis 1 — verify

## 이번 라운드 범위

CONTROL_SEQ 1490 이후 완료된 세 개 작업 라운드 검증.

| 라운드 | work note | 수정 파일 |
|--------|-----------|----------|
| M110 Axis 1 | m110-review-queue-search-filter.md | `ReviewQueuePanel.tsx` |
| Controller lane state truth | controller-lane-state-truth.md | `cozy.js`, `pipeline_gui/{app,backend,home_controller,home_presenter}.py`, `tests/test_controller_server.py`, `tests/test_pipeline_gui_home_presenter.py` |
| Pipeline runtime resume guard | pipeline-runtime-resume-guard.md | `pipeline_runtime/cli.py`, `tests/test_pipeline_runtime_cli.py` |

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile pipeline_runtime/cli.py pipeline_gui/{app,backend,home_controller,home_presenter}.py` | **PASS** |
| 회귀 테스트 4개 (zombie pidfile, lane state truth, ready-lane-not-working, recovery-verify-over-compat) | **PASS** |
| 전체 5개 test suite (test_pipeline_runtime_cli + test_pipeline_gui_home_presenter + test_pipeline_gui_home_controller + test_pipeline_gui_backend + test_controller_server) | **PASS — 136 tests** |
| `git diff --check` (10개 수정 파일 전체) | **PASS** |
| `cd app/frontend && npx tsc --noEmit` (ReviewQueuePanel.tsx 포함) | **PASS — exit 0** |

## Dirty tree 현황 (10개 파일)

| 분류 | 파일 |
|------|------|
| M110 Axis 1 | `app/frontend/src/components/ReviewQueuePanel.tsx` |
| controller truth | `controller/js/cozy.js` |
| pipeline GUI | `pipeline_gui/app.py`, `pipeline_gui/backend.py`, `pipeline_gui/home_controller.py`, `pipeline_gui/home_presenter.py` |
| controller test | `tests/test_controller_server.py`, `tests/test_pipeline_gui_home_presenter.py` |
| runtime guard | `pipeline_runtime/cli.py`, `tests/test_pipeline_runtime_cli.py` |

## 남은 리스크

- `ReviewQueuePanel.tsx` dist 미반영 — M110 Axis 2에서 처리 예정
- `review-queue-search-input` E2E 시나리오 미추가 — Axis 2와 함께 처리
- controller/runtime 수정은 Python/JS 런처 수준 변경으로 product docs 불영향; 별도 doc-sync 불필요
- Playwright 실제 실행은 CI 위임 (sandbox socket 제한)
