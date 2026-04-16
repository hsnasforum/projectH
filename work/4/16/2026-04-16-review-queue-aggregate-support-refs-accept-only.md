# review-queue aggregate support refs accept-only bundle

## 변경 파일

- `app/serializers.py`
- `tests/test_web_app.py`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/NEXT_STEPS.md`

## 사용 skill

- 없음

## 변경 이유

review-action root-doc drift는 이전 라운드들에서 전부 닫혔습니다. 그러나 `app/serializers.py`의 `_build_recurrence_aggregate_review_ref` 호출 시점에서 aggregate `supporting_review_refs` 수집이 review action을 구분하지 않아, `reject`/`defer` 결과도 aggregate support로 노출되고 있었습니다. Docs는 일관되게 "review record가 confidence support가 될 수 있다"고만 기술하고 accept-only 제한을 명시하지 않았습니다. 이번 라운드는 코드에서 accept-only 필터를 추가하고, 해당 제한을 docs에 명시하며, reject/defer 억제 regression test를 추가합니다.

## 핵심 변경

1. **`app/serializers.py`** (line 4033 부근): `supporting_review_refs` list comprehension에 `review_action == "accept"` 필터 추가. reject/defer review outcome은 source-message audit-only로 남고 aggregate support에 나타나지 않음.
2. **`tests/test_web_app.py`**: `test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs` 신규 추가. 두 source message를 각각 reject/defer로 review한 뒤 aggregate에 `supporting_review_refs`가 없음을 검증.
3. **`docs/ARCHITECTURE.md`** (line 813): "candidate_review_record only as confidence support" → accept-only 명시, reject/defer audit-only 명시.
4. **`docs/PRODUCT_SPEC.md`** (line 1071): 동일 수정.
5. **`docs/NEXT_STEPS.md`** (line 110): 동일 수정.
6. **`docs/ACCEPTANCE_CRITERIA.md`** (line 827, 857): accept-only support 명시, reject/defer 제외 명시.

## 검증

- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only` → OK (기존 accept-support regression 유지)
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_reject_defer_do_not_surface_as_supporting_review_refs` → OK (신규 reject/defer 억제 regression)
- `git diff --check -- app/serializers.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/NEXT_STEPS.md docs/ARCHITECTURE.md work/4/16` → clean

## 남은 리스크

- `reject`/`defer` outcome이 aggregate `supporting_review_refs`에서 제외되는 것은 source-message level의 `candidate_review_record` 자체에는 영향 없음. source-message level에서 reject/defer 기록은 그대로 유지됨.
- aggregate-level `reviewed_memory_boundary_draft`와 downstream contract chain은 `supporting_review_refs`가 비어 있을 때도 정상 동작함 (optional field). 다만 reject/defer-only aggregate에서 confidence support 없이 reviewed-memory apply가 열리는 시나리오는 아직 현재 구현에서 발생하지 않음 (promotion이 blocked 상태).
