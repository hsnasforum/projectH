# Gemini Advisory: browser investigation quality synthesis recommendation (2026-04-17)

## 1. 상황 요약
- **Investigation Ranking 고도화 완료**: `CONTROL_SEQ: 285` 슬라이스에서 `entity-card` 재조사 제안 순위를 `(status, sub_rank, slot_rank, stored_index)` 기준으로 정렬하는 로직이 성공적으로 구현 및 검증되었습니다.
- **Next Axis Ambiguity**: `docs/TASK_BACKLOG.md`의 "Current Phase In Progress"에는 여전히 다수의 web investigation 품질 개선 항목이 남아 있습니다. 특히 "Prefer multi-source agreement over single-source noise"와 "Distinguish strong facts, single-source facts, and unresolved slots" 사이의 우선순위 결정이 필요합니다.
- **Synthesis 레이어의 한계**: 현재 `core/web_claims.py`의 합성 로직은 단순히 출처 개수(support_count)가 2개 이상이면 `STRONG`으로 표시합니다. 이는 신뢰도 낮은 출처들 간의 "노이즈 합의"를 강력한 사실로 오인하게 할 리스크가 있습니다.

## 2. Arbitration 결과
- **Browser Investigation Family 유지**: 현재 프로젝트의 주력 품질 축인 브라우저 조사 품질 개선을 계속 이어가는 것이 타당합니다.
- **Next Axis Recommendation**: **Trusted-source weighted synthesis**를 제안합니다. 단순히 개수만 따지는 것이 아니라, 합의(agreement) 내에 신뢰할 수 있는 출처가 포함되어 있는지 여부를 따져 `STRONG` 상태를 더 엄격하게 정의합니다.

## 3. 권고 Slice
- **RECOMMEND: implement trusted-agreement requirement and conflict-sensitive status for entity-card claim synthesis**
- **이유**: `GEMINI.md`의 우선순위(`current-risk reduction > same-family user-visible improvement`)에 따라, 잘못된 정보가 `STRONG`으로 표시되는 리스크를 줄이고 사실 신뢰도를 사용자에게 더 명확히 전달하는 것이 가장 가치 있는 다음 단계입니다.
- **Strict Scope Limits**:
  - `core/web_claims.py` 내의 `_claim_sort_key` 및 `summarize_slot_coverage` 로직 수정.
  - `STRONG` 등급 기준에 `TRUSTED_CLAIM_SOURCE_ROLES` 포함 여부 추가.
  - 동일 슬롯 내 상반된 `STRONG` 후보 간의 충돌 감지 로직 추가 (충돌 시 `WEAK`로 강등하여 재조사 유도).
  - UI 레이아웃이나 `CoverageStatus` enum 수정은 포함하지 않음 (기존 status 범위 내에서 정확도 개선).
- **Narrowest Required Verification**:
  - `core/web_claims.py`에 대한 다양한 출처 조합(Trusted 1 vs Untrusted 2 등) 테스트 케이스 추가.
  - 기존 `reinvestigation` 및 `claim_coverage` Python 유닛 테스트 회귀 확인.

## 4. 기대 효과
- "노이즈 합의"에 의한 오보 가능성을 차단합니다.
- 재조사 제안 로직(`core/agent_loop.py`)이 더 신뢰할 수 있는 `fragility` 신호를 바탕으로 동작하게 됩니다.
