# 2026-05-08 M121 Direction (Watcher Lease Stability) — advisory

## STATUS: advice_ready
## CONTROL_SEQ: 1557

---

## 개요
M119-M120에 걸친 '주입-교정 피드백 루프(Injection-Correction Feedback Loop)' 아크가 UI 배지와 강등 안내 툴팁까지 포함하여 성공적으로 완료되었습니다. 모든 변경사항은 PR #113~#116으로 분절되어 대기 중이며, 최근 NBSP fix 과정에서 식별된 Watcher self-restart 시의 lease TTL 대기 리스크가 차기 주요 해결 과제로 남아 있습니다.

## 추천 사항
**RECOMMEND: implement M121 Candidate A (Watcher self-restart lease 구조 개선)**

### 근거
1. **리스크 감소 (Risk Reduction)**: `watcher_core.py` 내의 "supervisor 비정상 종료 시 stale lease가 TTL 만료 전까지 해제되지 않는다"는 주석이 명시하듯, self-restart 발생 시 최대 600~900초의 불필요한 대기가 발생할 수 있는 구조적 결함이 있습니다. 이는 런타임 안정성과 인시던트 회복 속도에 직결되는 문제입니다.
2. **아크 전환기 안정화 (Stabilization Phase)**: 주요 사용자 가치 기능인 M119-M120 아크가 마무리된 현재, 다음 기능 아크(Candidate B)로 넘어가기 전에 기반이 되는 `pipeline_runtime`의 기술 부채를 해결하고 안정성을 확보하는 것이 장기적인 품질 유지에 유리합니다.
3. **명확성 (Clarity)**: 후보 B(신규 기능)는 아직 구체적인 요구사항 정의가 필요한 단계인 반면, 후보 A는 명확한 재현 경로와 개선 목표를 가진 인프라 슬라이스입니다.

## 실행 전략 (Implement Handoff 힌트)
- **대상 파일**: `watcher_core.py`, `watcher_dispatch.py`.
- **내용**:
    - `PaneLease` 초기화 또는 self-restart 경로에서 동일한 supervisor identity를 가진 stale lease를 감지하고, 이를 안전하게 즉시 회수(reclaim)하거나 강제 해제(force release)하는 메커니즘을 구현합니다.
    - Lease TTL 정책을 restart 시나리오에 한해 동적으로 조정하거나, heart-beat 기반의 활성 확인 로직을 강화합니다.
- **검증**:
    - `tests/test_watcher_core.py`에 '기존 active lease가 존재하는 상태에서 신규 Watcher 인스턴스가 실행될 때 즉시 권한을 획득하는지' 확인하는 회귀 테스트 케이스를 추가합니다.

## 병행 권고 (PR Merge Gate)
현재 쌓여 있는 PR #113, #114, #115, #116 draft 스택은 `pr_merge_gate` operator 승인이 필요합니다. M121 구현 라운드와 병행하거나 직후에 verify/handoff owner가 이를 `bundle_merge`로 통합하여 정리하도록 권장합니다.

## 다음 단계
1. **M121 Candidate A 구현**: 런타임 안정성 슬라이스 진행.
2. **PR Merge Gate**: #113~#116 병합 및 브랜치 정리.
3. **M121 이후 아크 정의**: 인프라 안정화 완료 후 TASK_BACKLOG의 M121 이후 제품 가치 슬라이스 구체화.
