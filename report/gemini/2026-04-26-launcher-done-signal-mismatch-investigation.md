# Advisory Log: 2026-04-26 Launcher Slice 완료 및 signal_mismatch 조사 수렴

## 요약 (Summary)

Pipeline launcher의 hibernate surface 구현 및 검증이 완료되었습니다. 런처와 컨트롤러가 운영자 개입이 필요 없는 자동 대기 상태(`hibernate`, `operator_eligible=false`)를 정확히 구분하여 표시하게 되었습니다. 그러나 구현 직후 런타임에서 `signal_mismatch` 주의(attention) 상태가 보고되었습니다.

## 현재 상태 (Current Status)

- **완료**: Launcher/Controller hibernate 표시 로직 (`_truthy_flag`, `suppressedOperatorCandidate`)
- **검증**: Unit tests (32) 및 Playwright smoke (4) 통과 (로컬 환경 제약으로 일부 수동 보완)
- **이슈**: `automation_health = attention`, `reason = signal_mismatch` 발생

## 후보 비교 (Candidates)

### 후보 A: `signal_mismatch` 조사 및 해결 (권고)
- **성격**: Same-family current-risk reduction.
- **이유**: 방금 완료한 런처/런타임 표면 작업 직후 발생한 런타임 이슈입니다. `GEMINI.md`의 최우선 순위인 "동일 계열의 현재 리스크 감소"에 해당하며, M45로 축을 옮기기 전에 자동화 안정성을 확보하는 것이 타당합니다.
- **예상 작업**: `.pipeline/runs/*/events.jsonl` 및 wrapper-events 분석, 원인 식별 및 필요 시 보정.

### 후보 B: M45 방향 작업 전환
- **성격**: New quality axis / Milestone shift.
- **이유**: M44 closure 이후 예정된 계획입니다.
- **리스크**: 현재 런타임의 `signal_mismatch` 원인이 불명확한 상태에서 새 축으로 이동할 경우, 기존 자동화 가드 로직의 결함이 누적될 위험이 있습니다.

## 권고 (Recommendation)

**후보 A(`signal_mismatch` 조사)를 우선 실행할 것을 권고합니다.**

`signal_mismatch`는 Supervisor와 Wrapper 간의 상태 동기화 실패를 의미하며, 이는 런타임 신뢰성의 핵심 지표입니다. 런처의 표시 레이어를 수정한 직후 이 이슈가 부상했다는 점은, 수정 사항이 의도치 않은 신호 불일치를 유도했거나 혹은 그동안 숨겨져 있던 동기화 결함이 표면화되었을 가능성을 시사합니다. 이를 먼저 좁게(narrow) 해결한 뒤 M45로 전환하는 것이 `GEMINI.md` 기준에 부합합니다.

---
**STATUS**: advice_ready
**CONTROL_SEQ**: 289
