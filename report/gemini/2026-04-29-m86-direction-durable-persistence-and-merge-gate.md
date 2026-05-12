# 2026-04-29 M85 Completion and M86 Durable Persistence Direction Advisory

## 현황 및 완료 사항 (M85 Axis 3)
- **dist 재빌드**: M85 Axis 2에서 반영된 `is_highly_reliable` 승격 결과 UI가 `app/static/dist/assets/index.js`에 정상 반영되었습니다.
- **E2E 격리 검증**: 반복 교정 승격 시 "신뢰도 높음" 피드백이 표시되는 시나리오가 Playwright 격리 환경에서 성공(1 passed)했습니다.
- **Automation Health 보강**: `IMPLEMENT_ACTIVE` 상태에서 작업이 멈춘 경우(READY/prompt_visible 지속) `implement_active_idle` 어텐션 신호를, 타임아웃 후 재시도 대기 시 `idle_release_pending` 신호를 송출하여 silent stall을 방지하는 로직이 추가되었습니다.
- **문서화**: `.pipeline/README.md`에 no-silent-stall 계약이 명시되었습니다.

## 권장 사항

### 1. 머지 게이트 해소 (Operator Decision)
**RECOMMEND: needs_operator PR #71–#75 머지 실행**
- M85의 모든 축(Axis 1~3)과 fix(#71), docs(#72)가 retarget bundle로 준비되어 있습니다.
- `operator_request.md` (CONTROL_SEQ 1317)에 따라 전체 스택을 `master`(또는 `main`)에 머지하여 진실성(Truth-sync)을 확보하십시오.

### 2. M86 차기 방향 (Advisory Recommendation)
**RECOMMEND: implement M86 Axis 1 (Durable Preference Persistence)**
- **이유**: North Star 목표인 "cross-session memory 강화"를 위해, 현재 세션 로컬 수준에 머물러 있는 후보(Candidate) 저장 구조를 더 견고하고 지속적인(Durable) 형태로 정교화할 시점입니다.
- **슬라이스 범위**: Durable Candidate Storage 스키마 확장 및 SQLite 저장소 정교화.

## 리스크 및 주의사항
- **런타임 재시작**: `automation_health` 보강 로직은 supervisor/watcher 재시작 전까지는 live status에 반영되지 않습니다. PR 머지 후 런타임 재시작을 권장합니다.
- **브랜치 정규화**: 머지 완료 후 모든 로컬 작업트리를 최신 상태로 동기화한 뒤 M86 구현을 시작하십시오.
