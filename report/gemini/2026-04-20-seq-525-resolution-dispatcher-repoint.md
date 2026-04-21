# 2026-04-20 seq 525 resolution: dispatcher-repoint resolution

## 요약
- **RECOMMEND**: `RESOLVE-B` (Rename and Flip tests)
- **대상**: `pipeline_runtime/schema.py` (fallback 제거) 및 `tests/test_pipeline_runtime_schema.py` (테스트 2개 rename/flip + 1개 신규 추가)

## 결정 배경
1. **위험 감소 (G7)**: Gemini 523에서 식별된 `dispatcher-repoint` 버그의 핵심인 singleton fallback(`candidate_count == 1`) 제거가 필요합니다.
2. **검증 진실성 유지**: `RESOLVE-B`는 기존 fallback에 의존하던 테스트를 삭제하는 대신, 새 컨트랙트 하에서 "참조가 없으면 None을 반환한다"는 것을 증명하는 negative test로 전환합니다. 이는 단순 삭제(RESOLVE-A)보다 높은 테스트 밀도와 regression 방지 능력을 제공합니다.
3. **가이드라인 준수**: `/verify` README의 'overlapping candidates with low-confidence prioritization' 상황에서, truth-sync를 유지하며 시스템의 명시적 동작을 강화하는 방향을 선택했습니다.

## 상세 권고 (Pinning)
### 1. `pipeline_runtime/schema.py` 수정
- `:377-378`: `candidate_count` 및 `latest_any_refs` 로컬 변수 정의 제거.
- `:387`: loop 내부 `candidate_count += 1` 제거.
- `:392`: loop 내부 `latest_any_refs = refs` 제거.
- `:415-416`: singleton fallback 분기(`if candidate_count == 1 and not latest_any_refs: return latest_any`) 전체 제거.

### 2. `tests/test_pipeline_runtime_schema.py` 수정
- `:402` `test_falls_back_to_single_same_day_verify_without_reference`
  -> `test_returns_none_when_single_same_day_verify_has_no_reference`로 rename.
  - `:421` `self.assertEqual(resolved, verify_path)` -> `self.assertIsNone(resolved)`로 flip.
- `:446` `test_cross_day_unrelated_verify_does_not_replace_same_day_fallback_rule`
  -> `test_returns_none_when_same_day_unreferenced_and_cross_day_unrelated_both_present`로 rename.
  - `:471` `self.assertEqual(resolved, same_day_verify)` -> `self.assertIsNone(resolved)`로 flip.
- **신규 테스트 추가**: `LatestVerifyNoteForWorkTest` 클래스 끝에 `test_returns_none_when_lone_unrelated_same_day_verify_mimics_manual_cleanup` 추가 (seq 524 handoff 내용 반영).

## 다음 단계
- seq 526에서 위 변경 사항을 one-shot으로 구현합니다.
- 구현 후 `LatestVerifyNoteForWorkTest`의 총 테스트 메서드 개수는 7개가 되어야 합니다 (기존 6개 + 신규 1개).
