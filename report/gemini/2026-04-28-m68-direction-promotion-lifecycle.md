# Advisory Log: 2026-04-28 — M67 완료 및 M68 패턴 기반 승격 방향 권고

## 개요
M67 (Correction List Recent View) 마일스톤이 Axis 1+2를 통해 성공적으로 검증 및 커밋되었습니다. 또한, PR 머지 이후 발생했던 파이프라인 스톨(stall) 문제를 해결하기 위한 watcher recovery 작업(`work/4/28/2026-04-28-pr-merge-recovery-no-next-control.md`)이 완료되어 현재 working tree에 반영되어 있습니다. 본 advisory는 M67의 성과를 정리하고, 검증된 교정 데이터를 실제 시스템 지능으로 전환하는 M68 마일스톤 방향을 확정합니다.

## 분석 및 상태 확인
- **M67 완료**: 최근 교정 기록 3건을 PreferencePanel에 노출하고 E2E 검증을 마쳤습니다 (commit `094bd35`).
- **Watcher Recovery**: PR #53 머지 이후 `pr_merge_completed` 상태에서 다음 제어(control)를 생성하지 못하던 문제를 `watcher_core.py` 수정을 통해 해결했습니다. 해당 변경분은 현재 uncommitted 상태로 남아 있습니다.
- **M68 필요성**: 현재 시스템은 운영자가 교정 패턴을 승인(`CONFIRMED`)하거나 무시(`STOPPED`)할 수 있는 UI를 갖추었으나, 승인된 패턴이 실제 응답에 영향을 주는 `PreferenceRecord`로 즉시 전이되는 "Promotion" 경로가 누락되어 있습니다.

## 권고 사항
`RECOMMEND: implement M68 Axis 1 — Pattern-level promotion to Preference`

### 권고 근거
1. **생명주기 완성 (Lifecycle Closure)**: 교정(Correction) -> 검증(Validation) -> 승격(Promotion) -> 적용(Application)으로 이어지는 Reviewed-Memory 루프의 마지막 고리를 연결합니다.
2. **운영 효율성**: 자동 승격 임계치(예: 2개 이상의 세션 감지)를 기다리지 않고, 운영자가 중요하다고 판단한 패턴을 즉시 시스템에 반영할 수 있는 명시적 경로를 제공합니다.
3. **Recovery 안정화**: 현재 dirty 상태인 watcher recovery 변경분을 M68 Axis 1의 첫 커밋으로 포함하여 런타임 안정성을 확보해야 합니다.

### M68 Axis 1 상세 가이드
- **기능**: 운영자가 `CONFIRMED` 상태인 패턴에 대해 "승격(Promote)"을 실행하면, 해당 패턴을 `PROMOTED`로 상태 변경하고 `PreferenceStore.record_reviewed_candidate_preference()`를 호출하여 `PreferenceRecord`를 생성합니다.
- **Backend**: `POST /api/corrections/promote-pattern` 엔드포인트 구현.
- **Frontend**: `PreferencePanel.tsx`에서 `CONFIRMED` 배지 옆에 승격 버튼 및 처리 UI 추가.

## 결론
M67의 가시성 확보 성과를 기반으로, 실제 시스템의 지식 기반을 확장하는 M68 Axis 1 진행을 권고합니다. 다음 구현 라운드에서는 uncommitted recovery 변경분을 함께 번들링하여 커밋할 것을 권장합니다.
