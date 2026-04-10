# docs: ARCHITECTURE ACCEPTANCE_CRITERIA metadata panel empty-state truth sync

## 변경 파일
- `docs/ARCHITECTURE.md` — 응답 페이로드 테이블(line 157-160)에서 4개 메타데이터/패널 필드에 기본-빈 상태 명시
- `docs/ACCEPTANCE_CRITERIA.md` — Response Payload Contract 섹션(line 119)에서 메타데이터 필드 요약에 nullable/기본-빈 주석 추가

## 사용 skill
- 없음 (docs-only 슬라이스)

## 변경 이유
- 이전 슬라이스에서 `docs/PRODUCT_SPEC.md`의 동일 필드는 이미 `(default [], never null)` / `(default "", never null)`로 정확하게 기술
- `docs/ARCHITECTURE.md`와 `docs/ACCEPTANCE_CRITERIA.md`만 generic 표기로 빈-상태 계약 미명시
- 3개 문서 간 정합 필요

## 핵심 변경
- ARCHITECTURE 테이블: `evidence`, `summary_chunks`, `claim_coverage`에 `(default [])`, `claim_coverage_progress_summary`에 `(default "")` 추가
- ACCEPTANCE_CRITERIA: 메타데이터 필드 요약에 각 필드별 `(nullable)` 또는 `(default [])` / `(default "")` 주석 추가

## 검증
- `git diff --check` — 공백 오류 없음
- 2개 파일, 5줄 변경 확인
- 코드, 테스트, 카운트, UI 변경 없음

## 남은 리스크
- 없음 — 응답 페이로드 메타데이터/패널 필드 빈-상태 진실 동기화가 3개 문서 모두에서 완료
