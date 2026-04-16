# 2026-04-16 reviewed-memory aggregate supersession/staleness 중재 보고서

## 결정 요약
다음 구현 슬라이스로 **same-family current-risk reduction: reviewed-memory aggregate supersession 및 staleness 로직**을 추천합니다.

## 중재 배경
- `work/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split.md` 라운드를 통해 oversized aggregate smoke가 성공적으로 분할되고 검증되었습니다.
- 다음 단계 후보로 'supersession/staleness (risk reduction)'와 'reject/defer UI parity (improvement)'가 대립하였으나, `GEMINI.md`의 우선순위 원칙(risk reduction > improvement)에 따라 데이터 무결성을 보호하는 staleness 처리를 우선하기로 결정했습니다.

## 기술적 권고 사항
1. **Staleness 계약 정의**:
   - Aggregate의 `supporting_candidate_refs` 중 하나라도 현재의 교정 패턴(pattern fingerprint)과 일치하지 않게 되면(새 교정 기록, 거절, 또는 삭제) 해당 aggregate는 stale한 것으로 간주합니다.
2. **구현 범위**:
   - Aggregate 직렬화 시점에 백엔드에서 candidate의 최신 상태를 검증하는 로직을 추가합니다.
   - Stale한 aggregate는 `검토 메모 적용 후보` 섹션에서 은퇴(retired)시키거나 명시적으로 차단하여 잘못된 메모가 적용되는 리스크를 제거합니다.
3. **검증 전략**:
   - Playwright smoke test를 추가하여, aggregate를 형성했던 교정 중 하나를 사용자가 다른 내용으로 수정했을 때 aggregate card가 자동으로 사라지거나 갱신되는지 확인합니다.

## 결론
이 슬라이스는 reviewed-memory family의 데이터 truthful 수준을 '현재 유효한 상태만 적용 가능'하도록 끌어올려, 시스템의 전반적인 신뢰도를 확보하는 데 필수적입니다. 이 작업이 완료된 후 `reject/defer`의 UI coexistence parity로 넘어가는 것이 안전합니다.
