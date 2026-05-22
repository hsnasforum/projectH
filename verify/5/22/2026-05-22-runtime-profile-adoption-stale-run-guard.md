# verify: 2026-05-22 runtime profile adoption stale run guard (2145)

## 대상 work
`work/5/22/2026-05-22-runtime-profile-adoption-stale-run-guard.md`

## 검증 결과: READY

---

## 코드 확인

| 항목 | 위치 | 확인 |
|---|---|---|
| `_PROFILE_ADOPTION_STALE_REASON`, `_PROFILE_ADOPTION_MISMATCH_REASON_CODE` 상수 | `supervisor.py:131-132` | ✓ |
| `_profile_adoption_status()` — running plan vs active profile plan 비교 | `supervisor.py:3030` | ✓ |
| mismatch 시 `state: "stale_runtime_plan"`, `reason_code` 기록 | `supervisor.py:3035` | ✓ |
| `_write_status()`에 `profile_adoption` 블록 포함 | `supervisor.py:2468` | ✓ |
| plan mismatch 시 `runtime_profile_adoption_stale` → `degraded_reasons` 추가 | `supervisor.py:2252-2260` | ✓ |
| `verify=Claude` running plan에서 Claude task hint 활성화 | `supervisor.py` | ✓ |

## 회귀 테스트

| 검사 | 결과 |
|---|---|
| `python3 -m py_compile supervisor.py tests/test_pipeline_runtime_supervisor.py` | PASS |
| `test_write_status_surfaces_stale_active_profile_runtime_plan` | PASS |
| `test_write_status_activates_claude_task_hint_for_verify_round_when_profile_current` | PASS |
| `test_write_status_activates_codex_task_hint_for_verify_round_without_control_slot` | PASS |
| `git diff --check` | PASS |

---

## 근본 원인 (trigger-6 PARTIAL)

trigger-6 재시작 시 profile 파일은 `verify=Claude`였으나 supervisor가 이전 session의 런타임 plan을 유지한 채로 실행되어 Codex lane으로 dispatch됐음. 2145 guard는 이 mismatch를 `profile_adoption.state: stale_runtime_plan`으로 status에 노출해 운영자가 재시작 필요 여부를 즉시 판단할 수 있게 함.

---

## 다음 단계: 새 supervisor로 재시작

2145 guard가 working tree에 있는 상태로 supervisor를 재시작하면:
1. 새 supervisor가 현재 `agent_profile.json` 읽음 (`verify=Claude`)
2. running plan에 verify=Claude 반영
3. `profile_adoption.state: current` (mismatch 없음)
4. `work/5/22/2026-05-22-runtime-profile-adoption-stale-run-guard.md`가 fresh dispatch 대상
5. Claude verify lane이 이 work를 받아 처리 → `TASK_DONE source=wrapper lane=Claude` 기대
