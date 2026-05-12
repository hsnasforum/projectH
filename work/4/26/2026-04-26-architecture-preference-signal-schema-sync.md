# 2026-04-26 architecture preference signal schema sync

## 변경 파일
- `docs/ARCHITECTURE.md`
- `work/4/26/2026-04-26-architecture-preference-signal-schema-sync.md`

## 사용 skill
- `doc-sync`: M44-M48 preference signal schema 변경을 architecture 문서에만 맞추는 데 사용했다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 closeout으로 남기는 데 사용했다.

## 변경 이유
- CONTROL_SEQ 376 handoff는 M44-M48 preference signal schema가 `docs/ARCHITECTURE.md`에 반영되지 않은 상태를 단일 파일 bounded bundle로 동기화하라는 범위였다.
- 기존 architecture 문서는 `applied_preferences` badge와 `list_preferences_payload()`의 기본 status/audit fields만 설명하고, reliability/quality/conflict signal fields와 applied-preference popover 표시를 빠뜨리고 있었다.

## 핵심 변경
- top-level response payload 표의 `applied_preferences` 설명에 fetched full-preference status, `last_transition_reason`, per-preference reliability stats, `고품질` badge 표시를 추가했다.
- `list_preferences_payload()` 설명에 `reliability_stats.applied_count` / `corrected_count`와 negative feedback labels (`incorrect` / `unclear`) 반영 기준을 추가했다.
- `quality_info`, `is_highly_reliable`, active-only aggregates (`total_applied`, `total_corrected`, `high_quality_active_count`, `highly_reliable_active_count`)를 schema 설명에 추가했다.
- `conflict_info`의 기존 `has_conflict` / `conflicting_preference_ids`와 additive `conflict_severity` (`high` / `normal` / `none`)를 architecture 문서에 반영했다.
- handoff boundary에 따라 `docs/MILESTONES.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, code, runtime files는 수정하지 않았다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 확인: `64ae83a17a9d6c86b6232924c779594771b006a9db7398f7bb25377ece586f7c`.
- `git diff --check -- docs/ARCHITECTURE.md` 통과.
- `rg -n "is_highly_reliable|conflict_severity|total_applied|total_corrected|high_quality_active_count|highly_reliable_active_count|last_transition_reason|reliability_stats|corrected_count|incorrect|unclear" docs/ARCHITECTURE.md`로 필수 field 언급을 확인했다.

## 남은 리스크
- 문서 전용 slice라 Python/unit/TypeScript/browser smoke는 실행하지 않았다.
- 작업트리에는 이전 라운드의 untracked `/work` 기록 파일들이 남아 있다. 이번 라운드는 `docs/ARCHITECTURE.md`와 이 closeout만 추가/수정했다.
- commit, push, branch/PR publish, PR #38-#43 merge는 수행하지 않았다.
