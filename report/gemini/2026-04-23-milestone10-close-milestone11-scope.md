# 2026-04-23 Milestone 10 Close & Milestone 11 Scoping

## 요약
- Milestone 10 "Local Operator Operation"의 3개 Axis(실제 쓰기, 백업 메커니즘, 감사 추정 검증)가 모두 완료되었습니다.
- 이에 따라 `docs/MILESTONES.md`에 Milestone 10 종료 기록을 추가하고, 다음 단계로 **작업 가역성 및 안전성(Reversibility & Sandbox)**을 다루는 Milestone 11의 범위를 제안합니다.

## 질문에 대한 답변

### Q1 — Milestone 10 종료 기록 추가

`docs/MILESTONES.md`의 Milestone 9 종료 지점(452라인 부근) 뒤에 다음 내용을 삽입합니다.

**삽입할 내용:**
```markdown

### Milestone 10: Local Operator Operation
- enable actual file write for `local_file_edit` under explicit approval
- implement first rollback logic for reversible local actions
- verify audit trail integrity for end-to-end operator effects
- Local file edit active write shipped: `execute_operator_action()` performs actual disk write when `content` present (seq 892)
- Reversible backup mechanism shipped: `is_reversible=True` + file exists -> backup saved to `backup/operator/`; `backup_path` preserved in outcome (seq 896)
- Audit trail verification shipped: end-to-end integration test in `tests/test_operator_audit.py` (seq 900)
- **Milestone 10 closed** (seqs 892–900): local file operation and backup foundation established; actual rollback restore and sandbox restrictions remain deferred
```

**삽입 지점**: `### Why This Is Later` 섹션 바로 앞 (현재 약 452라인).

---

### Q2 — Milestone 11 범위 제안

실제 파일 쓰기가 가능해진 현재 상태에서, 시스템의 안전성과 신뢰성을 완성하기 위해 **가역성 실현(Rollback)**과 **경로 제한(Sandbox)**을 다음 목표로 제안합니다.

#### Milestone 11: Operator Action Reversibility & Sandbox
- implement actual rollback restore for reversible file edits
- define path restriction rules (sandbox) for operator actions
- ensure rollback traces are observable in session history

**첫 번째 구현 슬라이스: rollback_local_file_edit_restore**
- **파일**: `core/operator_executor.py`, `core/agent_loop.py`, `tests/test_operator_executor.py`
- **변경 내용**: `core/operator_executor.py`에 `rollback_operator_action(record)` 함수를 추가하여 `backup_path`의 내용을 `target_id`에 덮어쓰도록 구현합니다. `agent_loop.py`에서 실패 또는 사용자 요청 시(미래) 이를 호출할 수 있는 기반을 마련합니다.
- **테스트**: `tests/test_operator_executor.py`에 파일을 쓰고 백업한 뒤, 롤백을 수행하여 원본 내용이 복구되는지 검증하는 테스트를 추가합니다.

**결정 이유**:
이미 디스크 쓰기 능력을 갖춘 시스템에서 발생할 수 있는 실수를 수습할 수 있는 **실질적인 복구 능력(Rollback Restore)**을 갖추는 것이 "개인화 모델 레이어"로 넘어가기 전 가장 우선순위가 높은 안전장치입니다.
