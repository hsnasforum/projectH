# 2026-04-22 eval fixture family field enrichment

## 변경 파일
- `data/eval/fixtures/approval_friction_001.json`
- `data/eval/fixtures/conflict_defer_trace_001.json`
- `data/eval/fixtures/correction_reuse_001.json`
- `data/eval/fixtures/explicit_vs_save_support_001.json`
- `data/eval/fixtures/reviewed_vs_unreviewed_trace_001.json`
- `data/eval/fixtures/rollback_stop_apply_001.json`
- `data/eval/fixtures/scope_suggestion_safety_001.json`
- `work/4/22/2026-04-22-eval-fixture-family-field-enrichment.md`

## 사용 skill
- `finalize-lite`: 필수 체크 통과 여부, 문서 동기화 범위, `/work` closeout 준비 상태를 구현 종료 전에 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 한국어 `/work` 기록으로 남겼습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 858이 seq 853의 family-specific `TypedDict` 필드에 맞춰 7개 service fixture를 보강하도록 지시했습니다.
- 각 fixture는 기존 6개 `EvalArtifactCoreTrace` core 필드만 갖고 있었으므로 family-specific 필드 2개씩을 추가했습니다.

## 핵심 변경
- `correction_reuse_001.json`에 `reused_artifact_id`, `reused_correction_id`를 추가했습니다.
- `approval_friction_001.json`, `reviewed_vs_unreviewed_trace_001.json`, `scope_suggestion_safety_001.json`에 각 family-specific 필드 2개를 추가했습니다.
- `rollback_stop_apply_001.json`, `conflict_defer_trace_001.json`, `explicit_vs_save_support_001.json`에 각 family-specific 필드 2개를 추가했습니다.
- 기존 core trace 필드, fixture family 값, eval axes 값은 제거하거나 변경하지 않았습니다.
- handoff 제약에 따라 Python source, test, docs 파일은 수정하지 않았습니다.

## 검증
- `python3 -m unittest tests.test_eval_loader -v` -> 7개 테스트 통과
- `git diff --check -- data/eval/fixtures/` -> 통과

## 남은 리스크
- 이번 라운드는 JSON fixture enrichment만 수행했으며 `eval/fixture_loader.py` validation 로직은 handoff 범위 밖이라 변경하지 않았습니다.
- 문서 동기화는 handoff에서 금지되어 수행하지 않았습니다. 필요하면 별도 verify/handoff 라운드에서 판단해야 합니다.
