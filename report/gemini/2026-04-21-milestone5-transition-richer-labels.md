# 2026-04-21 Milestone 5 Transition: Richer Labels

## 상황
- PR #25 (Automation Hardening) 병합이 완료되어 내부 런타임/자동화 축의 큰 덩어리가 닫혔습니다.
- 현재 코드베이스는 Milestone 5, 6, 7의 첫 번째 슬라이스(artifact_id, session_local_memory_signal, review_queue 등)가 이미 구현된 상태입니다.
- 운영 지침(Gemini seq 707/721)에 따라 이제 'Milestone 5 transition'을 통해 제품 내러티브(grounded brief contract)를 공고히 하는 제품 축 작업으로 복귀해야 합니다.

## 검토 결과
- **Backlog 동기화 필요**: `docs/TASK_BACKLOG.md`의 "Next To Add" 섹션 중 3번(`session_local_memory_signal`)과 5번(`review_queue_items`)은 이미 구현(Implemented 23, 24 등)되었으나 백로그 상단에 여전히 존재하여 혼선을 줄 수 있습니다.
- **다음 논리적 슬라이스**: "Recently Landed" 항목 중 13번(minimum approval_reason_record)과 16번(minimum corrected_outcome)은 현재 고정된 최소 라벨(`explicit_rejection`, `path_change`, `explicit_content_rejection`)만 지원합니다.
- **Milestone 5 목표 부합**: `docs/MILESTONES.md`의 Milestone 5 "still later" 항목은 "richer reject labels"를 명시하고 있으며, 이는 `TASK_BACKLOG.md` "Next To Add" 4번 항목과 일치합니다.

## 권고
`RECOMMEND: implement richer scoped reason labels for correction / reject / reissue outcomes`

1. **라벨 확장**: `core/contracts.py`에 `factual_error`, `awkward_tone`, `context_miss`, `format_error` (교정/거절용), `directory_preference`, `filename_preference` (재발행용) 등 구체적인 품질 지표 라벨을 추가합니다.
2. **핸들러 보강**: `app/handlers/feedback.py`에서 신규 라벨을 수용하도록 보강하고, `app/templates/index.html` 등의 UI/UX 상에서 이를 선택하거나 활용할 수 있는 토대를 마련합니다.
3. **문서 동기화**: 구현 작업 중 이미 완료된 백로그 항목(item 3, 5 등)을 정리하여 `docs/` 내의 제품 계약 문서가 실제 구현된 '진실'을 반영하도록 합니다.
