# 2026-04-22 Milestone 8 Axis 6 doc sync

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/22/2026-04-22-milestone8-axis6-doc-sync.md`

## 사용 skill
- `doc-sync`: CONTROL_SEQ 853 구현 결과를 현재 문서의 shipped/deferred 상태에 맞춰 좁게 동기화했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 854가 Milestone 8 family-specific trace TypedDicts shipped 상태를 `docs/MILESTONES.md`에 반영하도록 지시했습니다.
- 이전 구현 closeout `work/4/22/2026-04-22-eval-family-trace-typeddicts.md` 기준으로 Axis 6 shipped 라인을 추가해야 했습니다.

## 핵심 변경
- Axis 5 shipped 라인에서 `family-specific trace extensions`를 deferred 목록에서 제거했습니다.
- Axis 6 shipped 라인을 추가해 `core/eval_contracts.py`의 family-specific TypedDict 7개, `EVAL_FAMILY_TRACE_CLASS` 매핑, `eval/__init__.py` export를 seq 853 shipped로 기록했습니다.
- `CandidateReviewSuggestedScope` enum과 e2e stage는 여전히 deferred로 유지했습니다.
- handoff 제약에 따라 Python source, test, fixture, 다른 docs 파일은 수정하지 않았습니다.

## 검증
- `git diff --check -- docs/MILESTONES.md` -> 통과

## 남은 리스크
- 이번 라운드는 `docs/MILESTONES.md`의 Milestone 8 Axis 6 상태 기록만 동기화했습니다.
- fixture validation 로직, JSON fixture enrichment, e2e eval stage는 이번 handoff 범위 밖이라 변경하지 않았습니다.
