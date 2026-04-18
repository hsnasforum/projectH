# Gemini Advisory: docs family closure and operator cleanup recommendation (2026-04-09)

## 1. 상황 요약
- **중복 작업 감지**: `CONTROL_SEQ: 277`과 그 이전 슬라이스들이 다룬 `save_content_source` / `source_message_id` 소유권 동기화 및 `session_local_memory_signal` 요약 wording 동기화는 이미 `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`에 모두 반영되어 있습니다.
- **Micro-loop 임계치 도달**: 4월 9일 당일 동일 family(docs-only truth-sync) 작업이 3회를 훨씬 초과하여, 더 이상 작은 docs 슬라이스로 쪼개는 것은 `GEMINI.md` 가이드라인에 어긋납니다.
- **구현 정합성 확인**: `app/serializers.py`와 `app/static/app.js`를 확인한 결과, 최근 `verify`에서 제안되었던 `history-card claim-progress summary` surfacing 등도 이미 구현이 완료된 상태입니다.

## 2. Arbitration 결과
- **Current Family Closure**: `current-message fields / signals` 관련 docs family는 이제 충분히 truthful하며 닫힌 것으로 간주합니다.
- **Next Axis Recommendation**: `internal cleanup` 축으로 전환하여, 백로그에 남아 있는 `adoption/cutover docs cleanup`을 수행할 것을 권고합니다.

## 3. 권고 Slice
- **RECOMMEND: docs pipeline-runtime-docs adoption/cutover cleanup**
- **대상 파일**:
  - `docs/projectH_pipeline_runtime_docs/01_개발계획서.md`
  - `docs/projectH_pipeline_runtime_docs/02_요구사항_명세서.md`
  - `docs/projectH_pipeline_runtime_docs/04_QA_시험계획서.md`
  - `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - `docs/projectH_pipeline_runtime_docs/07_마이그레이션_체크리스트.md`
  - `docs/projectH_pipeline_runtime_docs/00_문서세트_안내.md`
- **목표**: 6h/24h soak test 관련 문구를 "historical baseline" 또는 "adoption-only gate"로 명확히 정리하고, 현재의 데일리 검증 표준이 `launcher live stability gate + incident replay + real work sessions`임을 명시합니다.

## 4. 기대 효과
- 불필요한 docs micro-loop를 끊고 백로그의 실제 운영 정리 작업을 진척시킵니다.
- 프로젝트가 adoption 단계를 넘어 실질적인 운영/검증 단계로 진입했음을 문서상으로 확정합니다.
