# verify: 2026-05-21 stale handoff #2084 incident containment

## 사고 요약

재시작 시 archived 상태였어야 할 implement_handoff.md #2084 (README docs-only)가
active control로 남아 watcher가 Codex lane에 재dispatch. Codex가 out-of-scope 파일을
수정하고 wrapper가 TASK_ACCEPTED를 emit했으나 TASK_DONE이 오지 않아 WORKING 고착.

## 조치 완료

| 항목 | 결과 |
|---|---|
| runtime stop | STOPPED, lane 전부 OFF |
| stale handoff 이동 | `.pipeline/archive/2026-05-21/implement_handoff.2084-stale-contained.md` |
| cozy.js (사고 산출물) | `git restore` 완료 — 2줄뿐 아니라 chromaKeyImage/AGENT_IMAGES 변경까지 포함됐던 것 확인 |
| e2e assertion 변경 | 한국어 UI 문구와 일치 — 유지 커밋 d906484 |
| tracked dirty | 없음 |

## 근본 원인 확인

`completed_implement_handoff_truth()`가 #2084를 완료로 탐지하지 못한 이유:

- work 기록: `work/5/21/2026-05-21-readme-safety-defaults-memory-boundary-doc-sync.md` ✓
- verify 기록: 해당 slice 이름으로 없음 ✗
  (존재하는 readme 관련 verify는 다른 slice 이름)

→ verify 증거 없이 work-only로 완료된 handoff는
  `completed_implement_handoff_truth()` 탐지를 통과하지 못하고
  재시작 시 재dispatch에 취약.

## 다음 개선 후보 (지금 당장 blocker 아님)

`completed_implement_handoff_truth()`에 work-only 완료 처리 추가:
- work/ 기록은 있지만 verify/가 없는 경우, handoff content의 목표 파일이
  실제로 수정됐으면 completed로 판단하는 경로
- 또는 verify 기록 없는 stale implement handoff를 fail-closed 처리하는 정책

operator_request.md #2072 HOLD_PUBLICATION 결정 기록:
- implement_handoff.md #2100으로 supersede 완료
- dirty bundle local-only 유지
