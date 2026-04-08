# Docs save-note approval/write task-log optional addenda truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`approval_requested`와 `write_note`의 optional mode-specific extras가 `optional mode-specific extras`로만 기술. 실제 코드는 `source_path` (file/source summary), `search_query` + `source_paths` (search summary)를 고정적으로 추가.

## 핵심 변경

### docs/ARCHITECTURE.md
- `approval_requested`: optional extras → `source_path` (file/source summary) or `search_query` + `source_paths` (search summary) 명시
- `write_note`: optional extras → `source_path` (file/source summary) or `search_query` (search summary) 명시

### docs/PRODUCT_SPEC.md, docs/ACCEPTANCE_CRITERIA.md
- ARCHITECTURE 참조 문구에 `source_path` or `search_query` mode addenda 언급 추가

## 검증

- 3개 문서 모두 `search_query` 포함 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- save-note task-log detail 문서화 완료. feedback/verdict/candidate action detail shape은 별도 범위.
