# 2026-04-19 legacy active-context backfill arbitration

## 상태 (STATUS)
- **Arbitration Result**: `family_closed`
- **Next Axis**: `Milestone 4 (Secondary-Mode Investigation Hardening)`

## 판단 근거
1. **구현 및 검증 완료**: `summary_hint_basis` 필드의 이동, 새 세션 기록 시점 적용, 그리고 legacy 데이터에 대한 load-time backfill이 store/service layer에서 모두 구현되고 SQLite parity를 포함하여 검증되었습니다.
2. **Diminishing Returns**: 오늘 이미 동일한 field family에 대해 3회의 implementation-backed round가 진행되었습니다. 여기서 Playwright를 통한 추가 E2E 증명이나 SQLite raw canonicalization(내부 정리)을 수행하는 것은 '미세 쪼개기(micro-slicing)'에 해당하며, 진척의 밀도가 낮습니다.
3. **리스크 제어**: 서비스 레이어의 테스트(`tests.test_web_app`)가 이미 JSON/SQLite 페이로드의 정확성을 고정하고 있으므로, 브라우저에서의 시각적 재확인 없이도 legacy drift는 실질적으로 닫힌 것으로 간주할 수 있습니다.
4. **품질 축 전환**: `GEMINI.md`의 우선순위에 따라, 보조 모드 탐색의 품질을 높이는 `Milestone 4`나 구조화된 교정 메모리의 핵심 구조를 다루는 `Milestone 6`의 다음 단계로 전환하는 것이 프로젝트 전체의 균형 있는 진척을 위해 유리합니다.

## 권고 (RECOMMENDATION)
- `summary_hint_basis` 관련 family를 여기서 닫습니다.
- 다음 라운드는 `docs/TASK_BACKLOG.md`에서 현재 `In Progress`로 관리 중인 **Milestone 4 (보조 모드 탐색 강화: 슬롯 커버리지 및 재탐색)** 축으로 전환하여 진척을 만들 것을 권고합니다.
