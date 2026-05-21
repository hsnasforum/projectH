# 2026-05-19 reviewed-memory transition mutation identity HTTP payload

## 변경 파일

- `tests/test_web_app.py`
- `work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-http-payload.md`

## 사용 skill

- `work-log-closeout`: handoff #1973 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1973`이 `/api/session` route payload에도 `transition_mutation_identity_requirement = canonical_transition_id_and_aggregate_fingerprint_required` marker가 유지되는지 검증하라고 지시했습니다.
- 직전 라운드의 serializer/service assertion은 통과했지만, 로컬 웹 쉘은 `/api/session` HTTP JSON을 소비하므로 route-facing 회귀 증거가 필요했습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `tests/test_web_app.py`에 `test_session_http_payload_exposes_transition_mutation_identity_requirement`를 추가했습니다.
- 테스트는 같은 세션에서 두 파일 요약 후 동일 correction을 제출해 `recurrence_aggregate_candidates`를 materialize합니다.
- `LocalOnlyHTTPServer`로 `/api/session?session_id=<session_id>`를 GET한 뒤 HTTP JSON payload의 `reviewed_memory_transition_audit_contract`를 검사합니다.
- HTTP payload에 기존 `transition_identity_requirement = canonical_local_transition_id_required`와 새 `transition_mutation_identity_requirement = canonical_transition_id_and_aggregate_fingerprint_required`가 함께 남는지 확인합니다.
- `app/web.py`와 `app/serializers.py`는 수정하지 않았습니다. route dispatch와 serializer가 이미 marker를 보존했습니다.

## 검증

- `python3 -m py_compile app/web.py app/serializers.py tests/test_web_app.py`
  - 통과: 출력 없음.
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_session_http_payload_exposes_transition_mutation_identity_requirement tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_require_two_distinct_source_messages_and_ignore_same_anchor_replays tests.test_web_app.WebAppServiceTest.test_recurrence_aggregate_candidates_keep_candidate_review_as_support_only`
  - 통과: `Ran 3 tests in 0.123s`, `OK`.
- `rg -n "transition_mutation_identity_requirement|canonical_transition_id_and_aggregate_fingerprint_required|test_session_http_payload_exposes_transition_mutation_identity_requirement" app/web.py app/serializers.py tests/test_web_app.py`
  - 통과: serializer marker와 새 HTTP payload regression, 관련 exact assertion 위치를 확인했습니다.
- `git diff --check -- app/web.py app/serializers.py tests/test_web_app.py work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-http-payload.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 `/api/session` HTTP JSON payload boundary만 잠근 focused regression입니다.
- Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
