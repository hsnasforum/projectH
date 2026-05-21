# 2026-05-19 reviewed-memory transition mutation identity payload marker

## 변경 파일

- `app/serializers.py`
- `tests/test_web_app.py`
- `tests/test_smoke.py`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-payload-marker.md`
- 기존 dirty context로 함께 검증한 파일
  - `README.md`

## 사용 skill

- `doc-sync`: 새 payload marker를 현재 제품/아키텍처/수용 기준 문서의 reviewed-memory transition identity 설명과 맞추기 위해 사용했습니다.
- `work-log-closeout`: handoff #1972 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1972`가 reviewed-memory transition audit contract에 backward-compatible payload marker를 추가하라고 지시했습니다.
- 직전 문서 동기화는 `transition_identity_requirement = canonical_local_transition_id_required`가 audit-contract label이고, 실제 mutation guard는 `canonical_transition_id`와 `aggregate_fingerprint`를 함께 요구한다고 설명했습니다.
- 이번 라운드는 그 구분을 문서 설명에만 두지 않고 payload 자체에도 `transition_mutation_identity_requirement = canonical_transition_id_and_aggregate_fingerprint_required`로 노출했습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `app/serializers.py`의 `reviewed_memory_transition_audit_contract`에 additive `transition_mutation_identity_requirement` 필드를 추가했습니다.
- 기존 `transition_identity_requirement = canonical_local_transition_id_required`는 호환성을 위해 유지했습니다.
- `tests/test_web_app.py`와 `tests/test_smoke.py`의 exact contract assertions에 새 marker 필드를 추가했습니다.
- `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/ARCHITECTURE.md`에 새 payload marker 이름과 의미를 반영했습니다.
- stop/reverse/conflict-check mutation 동작 자체는 변경하지 않았습니다. 이미 검증된 wrong-fingerprint guard를 read-only audit contract payload에 드러내는 변경입니다.

## 검증

- `python3 -m py_compile app/serializers.py tests/test_web_app.py tests/test_smoke.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_require_two_distinct_source_messages_and_ignore_same_anchor_replays tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only tests.test_smoke.SmokeTest.test_recurrence_aggregate_candidates_helper_requires_exact_identity_and_distinct_anchors`
  - 통과: `Ran 3 tests in 0.103s`, `OK`.
- `rg -n "transition_mutation_identity_requirement|canonical_transition_id_and_aggregate_fingerprint_required|transition_identity_requirement" app/serializers.py tests/test_web_app.py tests/test_smoke.py docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md README.md`
  - 통과: serializer, focused tests, product/architecture/acceptance docs에서 기존 label과 새 mutation marker가 확인되었습니다.
- `git diff --check -- app/serializers.py tests/test_web_app.py tests/test_smoke.py README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-payload-marker.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 read-only audit contract payload marker와 focused assertion/docs sync 범위입니다.
- Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
