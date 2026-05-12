STATUS: verified
CONTROL_SEQ: 288
BASED_ON_WORK: work/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md
BASED_ON_HANDOFF: .pipeline/implement_handoff.md CONTROL_SEQ 287
VERIFIED_BY: Claude
NEXT_CONTROL: advisory_request.md CONTROL_SEQ 288

---

# 2026-04-26 Pipeline Launcher Hibernate Surface 검증

## 이번 라운드 범위

launcher/controller 표시 레이어 구현 — `pipeline-launcher.py`, `controller/js/cozy.js`,
`controller/js/state.js`, `tests/test_pipeline_launcher.py`,
`e2e/tests/controller-smoke.spec.mjs`. approval/runtime 의미론 변경 없음.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `python3 -m py_compile pipeline-launcher.py` | **PASS** |
| `git diff --check` (변경 5개 파일) | **PASS** |
| `python3 -m unittest -v tests.test_pipeline_launcher` | **PASS** — 32 tests OK |
| Playwright `controller hides non-operator hibernate gate` | **PASS** — 1 test (5.9s) |
| Playwright `operator attention` (3 scenarios) | **PASS** — 3 tests |

## 구현 클레임 확인

| 클레임 | 확인 결과 |
|------|------|
| `_truthy_flag` 도입, `"false"` 오해 방지 | unit tests 32개 통과 — regression 없음 ✓ |
| canonical `none` + `operator_eligible=false`일 때 compat operator slot 무시 | `test_runtime_view_prefers_canonical_none_over_compat_operator_hibernate` PASS ✓ |
| controller attention board: non-operator hibernate 숨김 | Playwright 1 PASS ✓ |
| real `needs_operator` attention board 보존 | Playwright operator attention 3 PASS ✓ |
| `git diff --check` 후행 공백 없음 | `rg` + diff check 양쪽 PASS ✓ |

## 범위 미검증

- 전체 controller smoke (broad): 변경 범위가 operator attention board/launcher snapshot에 한정 — 생략 정당
- `signal_mismatch` attention 원인: work note가 별도 runtime 이슈로 명시, 이번 라운드 범위 밖

## Dirty Tree 상태

| 파일 | 상태 |
|------|------|
| `pipeline-launcher.py` | 수정됨, 미커밋 |
| `controller/js/cozy.js` | 수정됨, 미커밋 |
| `controller/js/state.js` | 수정됨, 미커밋 |
| `tests/test_pipeline_launcher.py` | 수정됨, 미커밋 |
| `e2e/tests/controller-smoke.spec.mjs` | 수정됨, 미커밋 |
| `work/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md` | untracked |
| `verify/4/26/2026-04-26-pipeline-launcher-hibernate-surface.md` | 이 파일 (untracked) |

M44 publish (2커밋): 계속 보류. 이번 implement에서 commit/push/PR 없음 ✓

## 남은 리스크

- `signal_mismatch` automation attention: work note에서 신규 발견, 별도 runtime 이슈로 남아 있음
- M44 2커밋 publish: operator gate 대기 중, 거절되지 않음

## 다음 행동

advisory_request CONTROL_SEQ 288 — launcher slice 완료 후 next priority 수렴:
signal_mismatch 조사 vs M45 방향 작업.
