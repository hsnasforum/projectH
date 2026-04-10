# docs: response payload metadata panel empty-state truth sync

## 변경 파일
- `docs/PRODUCT_SPEC.md` — Metadata And Panel Fields 섹션(line 312-315)에서 4개 필드에 기본-빈 상태 명시

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- `core/agent_loop.py:81-84`에서 `evidence`, `summary_chunks`, `claim_coverage`는 `field(default_factory=list)`, `claim_coverage_progress_summary`는 기본 `None`이나 직렬화 시 `""` 변환
- `app/serializers.py:55-56, 62-65`에서 리스트/문자열 형태로 직렬화
- `core/`, `app/`, `tests/` 전체에서 `=None` 할당 경로 없음
- 셸도 `[]` / `""` 폴백으로 소비
- 문서만 generic "list of ..." / "localized ..." 표기로 빈 상태 계약 미명시

## 핵심 변경
- `evidence`: `(default [], never null)` 추가
- `summary_chunks`: `(default [], never null)` 추가
- `claim_coverage`: `(default [], never null)` 추가
- `claim_coverage_progress_summary`: `(default "", never null)` 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 1개 파일, 4줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 메타데이터/패널 필드 빈-상태 계약 진실 동기화 완료
