# docs: reversible_effect_handle applied_effect_target shipped qualifier truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 3곳(line 1314, 1327-1328, 1484-1486): "future"/"later" 수식어 → "now-materialized"/"now-shipped"
- `docs/ARCHITECTURE.md` — 1곳(line 1089): "later local target" → "now-materialized"
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 1005, 1018): "later rollback-capability backer"/"later local target" → "now-materialized"

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `reviewed_memory_reversible_effect_handle`과 `reviewed_memory_applied_effect_target`는 이미 구체화됨:
  - `docs/PRODUCT_SPEC.md:1312-1313`: "current implementation now also evaluates/materializes"
  - `docs/ACCEPTANCE_CRITERIA.md:1003-1004`: 동일
- emitted transition record와 apply result도 이미 출하됨
- 그러나 동일 문서의 후속 행에서 "future"/"later"/"should stay" 수식어 잔존

## 핵심 변경
- PRODUCT_SPEC 3곳: "future real"→"now-materialized", "later internal handle"→"this internal handle", "later rollback-capability source should stay"→"is one now-materialized", "must later point to"→"points to", "any later emitted/apply"→"now-shipped"
- ARCHITECTURE 1곳: "later local target"→"now-materialized"
- ACCEPTANCE_CRITERIA 2곳: "later rollback-capability backer"→"now-materialized", "later local target"→"now-materialized"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 9줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 내부 핸들/타겟 shipped 수식어 진실 동기화 완료
