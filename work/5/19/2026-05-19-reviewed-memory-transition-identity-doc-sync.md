# 2026-05-19 reviewed-memory transition identity doc sync

## 변경 파일

- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/ARCHITECTURE.md`
- `work/5/19/2026-05-19-reviewed-memory-transition-identity-doc-sync.md`

## 사용 skill

- `doc-sync`: verified service/HTTP transition identity guard를 현재 제품 문서에 맞추되 코드·테스트·roadmap 범위로 넓히지 않기 위해 사용했습니다.
- `work-log-closeout`: handoff #1971 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1971`이 reviewed-memory transition identity 문서가 현재 구현 truth를 반영하도록 동기화하라고 지시했습니다.
- 직전 service/HTTP 회귀 검증은 stop, reverse, conflict-check mutation이 `canonical_transition_id`만이 아니라 요청 `aggregate_fingerprint`와 transition record의 `aggregate_identity_ref.normalized_delta_fingerprint`까지 함께 일치해야 진행된다는 것을 확인했습니다.
- 기존 문서의 `transition_identity_requirement = canonical_local_transition_id_required` 표현은 실제 mutation guard를 transition-id-only처럼 읽히게 할 수 있어, audit-contract label과 runtime mutation guard를 분리해 설명했습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `docs/PRODUCT_SPEC.md`에 audit-contract label은 유지하되, shipped transition mutation은 `canonical_transition_id`와 matching `aggregate_fingerprint`를 모두 요구한다고 명시했습니다.
- `docs/ACCEPTANCE_CRITERIA.md`에 stop-apply, reversal, conflict-visibility mutation이 wrong fingerprint 요청을 거부하고 active/stopped/reversed/conflict-visibility 상태를 변경하지 않아야 한다는 acceptance truth를 추가했습니다.
- `docs/ARCHITECTURE.md`에 handler/service mutation identity guard가 stored transition identity의 `canonical_transition_id`와 `aggregate_fingerprint`를 모두 비교한다고 정리했습니다.
- `README.md`의 current smoke scenario 목록에 wrong `aggregate_fingerprint` stop/reverse/conflict-check 요청이 상태를 변경하지 않는다는 현재 보장을 반영했습니다.
- `app/serializers.py`의 기존 payload literal인 `transition_identity_requirement = canonical_local_transition_id_required`는 이번 handoff 범위 밖 코드 변경 없이 유지하고, 문서에서 그 값이 audit-contract label임을 분리해 설명했습니다.

## 검증

- `rg -n "transition_identity_requirement|canonical_transition_id|aggregate_fingerprint|aggregate_identity_ref|normalized_delta_fingerprint|wrong-fingerprint" README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md`
  - 통과: 관련 문서 위치에서 audit-contract label과 aggregate-fingerprint mutation guard 문구가 함께 확인되었습니다.
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ACCEPTANCE_CRITERIA.md docs/ARCHITECTURE.md work/5/19/2026-05-19-reviewed-memory-transition-identity-doc-sync.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 docs-only truth sync입니다. 제품 코드, 테스트, runtime, controller, Playwright/E2E는 수정하거나 실행하지 않았습니다.
- `transition_identity_requirement` payload literal 자체는 여전히 `canonical_local_transition_id_required`입니다. 이번 문서 동기화는 그 값을 audit-contract label로 설명하고, 현재 mutation guard의 추가 fingerprint 요구사항을 별도 current behavior로 명시했습니다.
- 전체 unittest, Playwright/E2E, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
