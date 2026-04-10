# docs: selected_source_paths non-null list truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Content Fields 섹션에서 `selected_source_paths`의 `, or null` 제거, `(default [], never null)` 명시
- `docs/ARCHITECTURE.md` — 응답 페이로드 테이블에서 `list | null` → `list`, `(default [])` 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:75`에서 `selected_source_paths`는 기본값 `field(default_factory=list)`로 항상 리스트
- `app/serializers.py:48`에서 직접 직렬화, null 변환 없음
- `core/`, `app/`, `tests/` 전체에서 `selected_source_paths=None` 할당 경로 없음
- 이전 슬라이스에서 잘못 `, or null`을 추가한 것을 수정

## 핵심 변경
- PRODUCT_SPEC: `or null` → `(default [], never null)`
- ARCHITECTURE: `list | null` → `list`, `(default [])`

## 검증
- `git diff --check` — 공백 오류 없음
- `rg -n "selected_source_paths\s*=\s*None" core app tests` — 0건
- 2개 파일, 각 1줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — `selected_source_paths` 비-null 리스트 진실 동기화 완료
