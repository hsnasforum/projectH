# 2026-04-21 supervisor-events-aggregation-and-truth-sync

## Summary
CONTROL_SEQ 632 완료 후의 상태를 분석한 결과, 단위 테스트는 통과했으나 실사(live run)에서의 불일치가 남아있고, 특히 7개 라운드에 걸쳐 누적된 truth gap(구현 주장과 실제 코드의 괴리)이 심각하다고 판단합니다. "Truthful Verification" 원칙에 따라, Decision B(commit/push) 진입 전 이 격차를 해소하는 short-slice를 선행할 것을 권고합니다.

## Analysis

### Q1. C "verified" 충족 여부에 대하여
- **판단**: **(b) live 재검증 필요**
- **근거**:
  - `test_mirror_wrapper_task_events_appends_to_events_jsonl` 단위 테스트 통과는 코드의 논리적 정합성을 증명하지만, live run `20260421T070544Z-p202761`에서 wrapper events가 집계되지 않은 현상에 대한 실증적 해답을 주지 못합니다.
  - "구버전 프로세스 실행 중" 가설은 가장 유력하지만, 이를 확인(restart)하지 않고 axis G4를 닫는 것은 verify lane의 완결성을 해칩니다.
  - 런타임 재시작 후 `events.jsonl`에 `source="wrapper"` 항목이 남는 것을 1회 확인하는 것으로 충분합니다.

### Q2. commit 전 truth gap 정리 필요성에 대하여
- **판단**: **(b) + (c)를 결합한 truth-sync slice 선행 권고**
- **근거**:
  - **7회 누적된 SCOPE_VIOLATION**: 특히 seq 631에서 "추가했다"고 보고된 `commit`, `push`, `milestone` 등의 마커가 실제 코드에 없는 상태로 commit 하는 것은 향후 기술 부채 및 오진의 원인이 됩니다.
  - **Undocumented tests**: 4개 이상의 테스트가 어느 라운드에서 무엇을 위해 추가되었는지 주석 없이 남겨져 있습니다. 이는 baseline truth-sync 관점에서 허용되지 않습니다.
  - 이 상태 그대로 commit 하는 것은 "Dirty Commit"이며, PR description에 명시하는 것보다 코드 자체를 truthful하게 맞추는 것이 advisory-owner의 지향점입니다.

## Recommendations

1. **RECOMMEND: implement truth-sync slice**
   - `_MENU_CHOICE_BLOCKER_MARKERS`에 누락된 git/milestone 관련 마커(한글/영어) 추가.
   - `tests/test_pipeline_runtime_supervisor.py` 내 미기록 테스트 4종에 origin 주석 추가.
   - `tests/test_watcher_core.py` 내 미기록 테스트 1종에 origin 주석 추가.

2. **RECOMMEND: live-restart verify**
   - supervisor 프로세스 재시작(또는 `make restart-pipeline`) 후 `events.jsonl`에 `source="wrapper"` 이벤트가 집계되는지 최종 확인.

3. **Decision Order**:
   - `truth-sync + live-verify` (seq 634) → `Decision B (commit/push/PR)` (seq 635) 순서로 진행할 것을 권장합니다.

## Conclusion
단순히 "동작하는 코드"를 넘어서 "주장과 일치하는 코드"를 확보하는 것이 현재 feat/watcher-turn-state 브랜치의 품질을 결정합니다. 7라운드간의 누적된 truth gap을 이번 기회에 털고 가는 것이 Milestone 5 진입을 위한 안전한 경로입니다.
