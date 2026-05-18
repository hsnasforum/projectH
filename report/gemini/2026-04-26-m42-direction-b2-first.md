# Advisory Log: 2026-04-26-m42-direction-b2-first

## 요약
M41까지의 구현 사항(M38~M41)이 `feat/watcher-turn-state` 브랜치에서 기능적으로 완료되었으나, 핵심 문서(`PRODUCT_SPEC.md`, `ARCHITECTURE.md`, `ACCEPTANCE_CRITERIA.md`)에 해당 사양이 반영되지 않은 **deep-doc drift**가 확인되었습니다. 또한, 최근 3회 연속으로 `MILESTONES.md`만 갱신하는 micro-slice가 진행되어 `GEMINI.md`의 "3+ same-family docs-only" 규칙이 발동되었습니다. 이에 따라 다음 라운드에서 개별 기능을 추가하기보다, 누적된 구현 진실을 문서에 통합 반영하는 **B2 (Deep-Doc Bundle)** 진행을 권고합니다.

## 분석 및 판단
1. **리스크 감소 (Risk Reduction):** M39~M41에서 추가된 중요 필드(`context_turns`, `evidence_summary`, `source_session_title`, `reason_note`, `review_reason_note`, PreferencePanel audit block 등)가 상위 설계 문서에 누락되어 있어, 차기 마일스톤(M42) 진입 전 이 격차를 해소하는 것이 유지보수 리스크를 줄이는 데 가장 시급합니다.
2. **규칙 준수:** 3회 연속 소규모 문서 갱신 이후에는 bounded bundle 또는 escalation이 필요합니다. B2는 이 요구사항을 충족하는 적절한 "bounded bundle"입니다.
3. **M42 방향성:** Feature Track(A1/A2) 진입 전, 현재까지의 성과를 `main`에 병합하기 위한 준비 단계로서 B2(문서 동기화) -> B1(Release Gate/Merge 준비) 순서가 타당합니다.
4. **우선순위 결정 (Tie-break):** `GEMINI.md` 기준에 따라 "same-family current-risk reduction"(B2)을 "new quality axis"(A1)보다 우선합니다.

## 권고 사항
- **우선순위 1:** `B2 Deep-Doc Bundle`을 즉시 실행하여 M38~M41의 기술적 진실을 `docs/` 내 3대 문서에 반영하십시오.
- **우선순위 2:** B2 완료 후, `B1 Release Gate`를 통해 E2E 환경 검증 및 `feat` 브랜치의 `main` 병합을 준비하십시오 (staged 상태의 `MILESTONES.md` 커밋 포함).
- **우선순위 3:** 모든 통합 작업이 완료된 후, `A1 Preference Activation`으로 M42 feature track을 시작하십시오.

## Exact Slice 권고
- **TASK:** Implement B2 (Deep-Doc Bundle)
- **FILES:** `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`
- **CONTENT:** M38 (E2E healthcheck), M39 (Review Enrichment fields), M40 (Review Auditability fields), M41 (Preference Auditability & PreferencePanel audit block) 반영
