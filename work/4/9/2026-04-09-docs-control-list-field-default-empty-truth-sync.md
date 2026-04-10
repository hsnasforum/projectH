# docs: response payload control list field default-empty truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Control Fields 섹션(line 289, 294, 295)에서 3개 리스트 필드에 `(default [], never null)` 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:71, 79, 93`에서 `actions_taken`, `follow_up_suggestions`, `search_results` 모두 `field(default_factory=list)`로 항상 리스트
- `app/serializers.py:43, 52, 66-73`에서 리스트 형태로 직렬화
- `core/`, `app/`, `tests/` 전체에서 `=None` 할당 경로 없음
- 셸도 `[]` 폴백으로 소비(`app/static/app.js:999-1010, 3152, 3182, 3195, 3214`)
- 문서만 generic "list of ..." 표기로 null 가능성이 암묵적

## 핵심 변경
- `actions_taken`: `(default [], never null)` 추가
- `follow_up_suggestions`: `(default [], never null)` 추가
- `search_results`: `(default [], never null)` 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 3줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 제어 리스트 필드 기본-빈 계약 진실 동기화 완료
