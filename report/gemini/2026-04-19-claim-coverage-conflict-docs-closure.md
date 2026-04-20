# 2026-04-19 Claim Coverage Summary CONFLICT family closure arbitration

## 중재 배경
- seq 376~378을 통해 `CONFLICT` ("정보 상충") 상태가 storage, serializer, core, browser surface(히스토리 카드, 팩트 바, 라이브 세션 요약) 전 영역에 걸쳐 구현 및 검증됨.
- 현재 모든 브라우저 표면이 실제 데이터와 일치(truthful)하게 동작하며, Playwright 테스트로도 고정됨.
- `GEMINI.md`의 우선순위에 따라 current-risk 및 user-visible improvement가 달성되었으므로, 새 axis로 넘어가기 전에 문서 동기화(truth-sync)를 통해 이 family를 공식적으로 닫을 시점임.

## 결정 및 권고
- **RECOMMEND: implement Claim Coverage Summary CONFLICT — docs-only truth-sync bundle**
- **결정 이유**:
    - `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`, `docs/ACCEPTANCE_CRITERIA.md` 등이 아직 3-status 모델이나 placeholder 상태에 머물러 있어 실제 구현 상태와 괴리가 있음.
    - 이 괴리를 방치할 경우 다음 라운드에서 중복 작업이나 오해가 발생할 risk가 있음.
    - `core/agent_loop.py` 워딩 폴리싱 같은 마이크로 슬라이스를 별도로 진행하기보다, 문서를 일괄 업데이트하여 family 전체의 완료 상태를 확정하는 것이 "meaningful coherent slice" 관점에서 적절함.

## 상세 가이드
- **수정 대상 파일**:
    - `docs/MILESTONES.md`
    - `docs/TASK_BACKLOG.md`
    - `docs/ACCEPTANCE_CRITERIA.md`
- **범위 제한**:
    - Milestone 3 및 Task Backlog (항목 11, 12 등)에서 "color-coded fact-strength summary bar"를 "4-segment (strong/conflict/weak/missing)"로 구체화.
    - `CoverageStatus.CONFLICT` ("정보 상충") 상태가 storage부터 browser surface까지 풀 체인으로 지원됨을 명시.
    - Acceptance Criteria의 Web Investigation 섹션에서 4-status 모델과 각 브라우저 노출 지점(History, Bar, Live Session)의 일관성 기준 업데이트.
- **검증 명령**:
    - `grep -E "CONFLICT|정보 상충" docs/*.md`
    - `git diff --check`
