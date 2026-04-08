# Docs PRODUCT_SPEC ARCHITECTURE evidence summary_chunks field-shape truth sync

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`

## 사용 skill

- 없음

## 변경 이유

`evidence`와 `summary_chunks`가 두 문서에서 이름만 나열되어 있었고, 실제 직렬화 코드(`app/serializers.py:895-934`)가 반환하는 필드 shape이 기술되지 않았음. `evidence_snapshot`과 `summary_chunks_snapshot`도 snapshot 섹션에서 이름만 나열 상태였음.

## 핵심 변경

### docs/PRODUCT_SPEC.md, docs/ARCHITECTURE.md (message-level)
- `evidence`: `{label, source_name, source_path, snippet, source_role}` shape 기술
- `summary_chunks`: `{chunk_id, chunk_index, total_chunks, source_path, source_name, selected_line}` shape 기술

### docs/PRODUCT_SPEC.md (snapshot 2곳), docs/ARCHITECTURE.md (snapshot 1곳)
- `summary_chunks_snapshot`: same shape as message-level `summary_chunks` 참조
- `evidence_snapshot`: same shape as message-level `evidence` 참조

## 검증

- message-level, snapshot-level 총 10곳에서 field-shape 기술 확인
- `git diff --check`: whitespace 에러 없음

## 남은 리스크

- 세션 메타데이터의 주요 복합 필드(`response_origin`, `active_context`, `claim_coverage`, `web_search_history`, `evidence`, `summary_chunks`)가 모두 field-shape 기술 완료됨.
