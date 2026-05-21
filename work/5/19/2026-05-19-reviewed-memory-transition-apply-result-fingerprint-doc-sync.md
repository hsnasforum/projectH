# 2026-05-19 reviewed-memory transition apply/result fingerprint doc sync

## 변경 파일

- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `docs/PRODUCT_SPEC.md`
- `work/5/19/2026-05-19-reviewed-memory-transition-apply-result-fingerprint-doc-sync.md`

## 사용 skill

- `doc-sync`: apply/result wrong-fingerprint HTTP regression으로 확인된 현재 동작을 제품/아키텍처/수용 기준 문서에 맞추기 위해 사용했습니다.
- `work-log-closeout`: handoff #1977 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1977`이 reviewed-memory transition mutation identity 문서가 apply/result wrong-fingerprint guard까지 포함하도록 동기화하라고 지시했습니다.
- 직전 검증에서 `/api/aggregate-transition-apply`와 `/api/aggregate-transition-result`도 mismatched `aggregate_fingerprint` 요청을 HTTP 404로 거부하고 `applied_at`, `result_at`, `apply_result`, active effect를 변경하지 않는 regression이 통과했습니다.
- 기존 문서 일부는 wrong-fingerprint mutation guard를 stop/reverse/conflict 중심으로 설명해 현재 테스트 truth보다 좁게 표현되어 있었습니다.

## 핵심 변경

- `docs/ACCEPTANCE_CRITERIA.md`의 transition mutation identity 설명을 모든 shipped transition mutation handler 기준으로 갱신했습니다.
- `docs/ARCHITECTURE.md`의 emitted-transition-record layer 설명을 apply/result-confirmation/stop/reverse/conflict-visibility 전체 wrong-fingerprint guard로 확장했습니다.
- `docs/PRODUCT_SPEC.md`에도 같은 current-truth drift가 직접 확인되어 scope 예외로 함께 동기화했습니다.
- 문서에는 `/api/aggregate-transition-apply`, `/api/aggregate-transition-result`, `/api/aggregate-transition-stop`, `/api/aggregate-transition-reverse`, `/api/aggregate-transition-conflict-check`가 모두 같은 `canonical_transition_id + aggregate_fingerprint` mutation identity guard를 요구한다고 명시했습니다.
- 제품 코드, 테스트, UI, route 이름, serializer field 이름은 변경하지 않았습니다.

## 검증

- `rg -n "transition_mutation_identity_requirement|canonical_transition_id_and_aggregate_fingerprint_required|aggregate-transition-apply|aggregate-transition-result|wrong-fingerprint|wrong fingerprint" docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md`
  - 통과: 세 문서에서 apply/result endpoint와 wrong-fingerprint guard 문구를 확인했습니다.
- `git diff --check -- docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md docs/PRODUCT_SPEC.md work/5/19/2026-05-19-reviewed-memory-transition-apply-result-fingerprint-doc-sync.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 문서 truth-sync 범위입니다.
- 전체 unittest, Playwright, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.
