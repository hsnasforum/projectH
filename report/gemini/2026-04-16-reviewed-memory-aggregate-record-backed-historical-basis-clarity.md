# 2026-04-16 reviewed-memory aggregate record-backed historical basis clarity 중재 보고서

## 결정 요약
다음 구현 슬라이스로 **same-family user-visible clarity: reviewed-memory aggregate record-backed historical basis clarity**를 추천합니다.

## 중재 배경
- `work/4/16/2026-04-16-reviewed-memory-aggregate-review-support-visibility-after-reject-defer.md` 라운드를 통해 aggregate card에 `검토 수락 N건 / 교정 M건`이라는 명시적인 review support line이 추가되었습니다.
- 현재 시스템은 aggregate가 transition record 발행(emitted) 단계에 진입하면, 기반이 된 교정(basis corrections)이 이후 supersession으로 인해 사라지더라도 해당 aggregate card를 유지하는 "record-backed lifecycle survival" 계약을 따릅니다.
- 이 경우 사용자는 "교정 0건" 또는 줄어든 카운트를 보게 되어 "왜 이 aggregate가 여전히 유효한지" 혼란을 느낄 수 있습니다. 이는 `GEMINI.md`에서 정의한 same-family user-visible clarity gap에 해당합니다.

## 기술적 권고 사항
1. **Historical Basis 명시**:
   - Aggregate card가 `record_stage` 상 `emitted_record_only_not_applied` 이후 단계(이미 발행됨)에 있고, 현재 라이브 세션의 `recurrence_count`나 `supporting_review_refs`가 발행 시점의 기대치보다 낮아진 경우(또는 단순하게 record-backed 상태인 경우), 이를 사용자에게 명확히 알립니다.
2. **UI 구현 범위**:
   - `app/static/app.js`에서 transition record가 존재할 때 `[기록된 기준]` 또는 `[Recorded Basis]` 형태의 배지/접두어를 review-support line에 추가합니다.
   - 이를 통해 사용자는 현재 라이브 메시지가 변했더라도, 이전에 확정한 기록을 바탕으로 적용(Apply)이 가능하다는 점을 인지할 수 있습니다.
3. **검증 전략**:
   - Playwright smoke test를 추가하여, aggregate 발행 후 기반 교정을 supersede했을 때 aggregate card가 사라지지 않고 `[기록된 기준]` 표식과 함께 유지되는지 확인합니다.

## 결론
이 슬라이스는 `reviewed-memory` 가족의 복잡한 상태 머신(record-backed survival)을 사용자에게 정직하게(truthful) 드러내는 마지막 퍼즐입니다. 이 작업이 완료되면 `reviewed-memory` 가족의 주요 리스크와 모호함이 해소되어 다른 `app.web` 축으로의 전환이 더 안전해집니다.
