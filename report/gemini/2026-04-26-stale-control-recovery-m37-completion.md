# 2026-04-26 stale-control-recovery-m37-completion

## 결정: 후보 A (M37 Axis 2 커밋 및 M38 방향 설정)

### 근거
1. **Stale Control 원인**: M37 Axis 2(Preference Count-Agnostic E2E) 검증이 완료되었으나, 이후 커밋 및 다음 단계로의 제어가 이뤄지지 않아 960 사이클 동안 정체되었습니다.
2. **검증 완료 상태**: 149개 E2E 테스트가 전수 패스되었고, SQLite 마이그레이션 및 개수 무관 assertion이 안정적으로 구현되었습니다.
3. **리스크 감소**: uncommitted 상태로 남아 있는 M37 Axis 2 변경사항(`e2e/tests/web-smoke.spec.mjs`)을 조속히 커밋하여 브랜치 안정성을 확보해야 합니다.

### 권고 Action (M37 Axis 3 및 Milestone 종결)
- **목표**: M37 작업을 커밋하고 Milestone 37을 공식적으로 종결.
- **실행 항목**:
    1. **Operator Request**: M37 Axis 2 변경사항을 커밋하고 `docs/MILESTONES.md`에 M37 완료 내역을 동기화(doc-sync)하도록 연산자에게 요청.
    2. **M38 방향**: M38에서는 **E2E 실행 환경 안정화(Isolation & Healthcheck)**를 통해 지속적인 테스트 flakiness 리스크를 근본적으로 제거할 것을 권고.
- **검증**: `git status` clean 확인 및 `docs/MILESTONES.md` 정합성 확인.

### 차기 Milestone (M38) 예고
- **Milestone 38**: Test Infrastructure Robustness
- **Axis 1**: `make e2e-test` 환경 개선 (start-server.sh wrapper 도입 및 포트 점유 대기 로직 강화).
