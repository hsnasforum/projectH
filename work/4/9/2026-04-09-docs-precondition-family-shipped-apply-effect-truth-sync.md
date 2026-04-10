# docs: reviewed-memory precondition family current-shipped apply/effect wording truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — 5곳(line 1473, 1483, 1490, 1492, 1493): "without opening apply" / "future applied" / "later effect-capability" / "before apply" → shipped 프레이밍
- `docs/ARCHITECTURE.md` — 3곳(line 858, 865, 871): "still missing every required precondition" / "future reviewed-memory effect" / "later applied effect" → shipped 프레이밍
- `docs/ACCEPTANCE_CRITERIA.md` — 2곳(line 648, 654): "later reviewed-memory effect" / "later applied effect" → shipped 프레이밍

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- reviewed-memory 전제조건 family의 의미 설명에서 apply/effect를 "future"/"later"/"unopened"로 프레이밍
- 실제로 apply result, stop-apply, reversal, conflict visibility 모두 이미 출하됨
  - `app/handlers/aggregate.py:392, 467, 529, 636`
  - `tests/test_web_app.py:7288, 7300`

## 핵심 변경
- PRODUCT_SPEC: "without opening promotion or apply" → "apply path is now shipped; promotion and cross-session counting remain later", "future/later" → 현재형
- ARCHITECTURE: "still missing every required precondition" → "precondition family gates the unblock path; apply path is now shipped above", "future" → 현재형
- ACCEPTANCE_CRITERIA: "later reviewed-memory effect" → "reviewed-memory effect", "later applied effect" → "applied effect"

## 검증
- `git diff --check` — 공백 오류 없음
- 3개 파일, 17줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 전제조건 family의 apply/effect shipped 문구 진실 동기화 완료
