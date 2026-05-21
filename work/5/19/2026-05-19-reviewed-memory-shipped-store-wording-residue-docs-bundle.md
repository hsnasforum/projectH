# 2026-05-19 reviewed-memory shipped store wording residue docs bundle

## 변경 파일

- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/5/19/2026-05-19-reviewed-memory-shipped-store-wording-residue-docs-bundle.md`

## 사용 skill

- `doc-sync`: shipped reviewed-memory lifecycle와 future/user-level/cross-session memory 경계를 문서에서 분리하기 위해 사용했습니다.
- `work-log-closeout`: handoff #1981 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1981`이 current-product docs의 reviewed-memory absent/future-only 잔여 문구를 bounded bundle로 정리하라고 지시했습니다.
- 현재 shipped 계약은 review queue, aggregate apply trigger, emitted/apply/result/active-effect path, explicit stop, reversal, conflict visibility를 포함합니다.
- 동시에 payload-visible reviewed-memory store, user-level memory, cross-session reviewed-memory application, broader structured correction memory는 아직 미출하 경계로 남아야 합니다.

## 핵심 변경

- `docs/PRODUCT_SPEC.md`의 “reviewed memory store가 없다” 문구를 payload-visible store/user-level/cross-session application 부재로 좁히고, shipped same-session reviewed-memory lifecycle은 이미 존재한다고 명시했습니다.
- `docs/ARCHITECTURE.md`의 review action API 문구를 `accept` / `reject` / `defer` / `edit` 전체 shipped action에 맞췄습니다.
- `docs/ACCEPTANCE_CRITERIA.md`에서 raw aggregate projection이 read-only인 점과 shipped reviewed-memory apply lifecycle이 별도 aggregate transition path 위에 있다는 점을 분리했습니다.
- 같은 문서의 promotion marker 문구를 shipped reviewed-memory transition lifecycle 또는 rollback result로 오해하지 않도록 갱신했습니다.
- `README.md`는 handoff의 검색/검증 대상에 포함했지만 이번 라운드에서 새로 수정하지 않았습니다.

## 검증

- `sha256sum .pipeline/implement_handoff.md`
  - 결과: PASS. 요청 SHA `9c56c5f7c8120396c0ed2becc07494225f7f8f97fdbc71437ce8d641ae269335`와 일치했습니다.
- `rg -n "no reviewed memory store|reviewed memory|reviewed-memory|aggregate-transition|active effect|review queue|explicit stop|conflict visibility" README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md`
  - 결과: PASS. shipped reviewed-memory lifecycle 문구와 future/user-level/cross-session 경계 문구를 확인했습니다.
- `rg -n 'current repo still does not implement a reviewed memory store|still has no `edit` API|does not create repeated-signal promotion, reviewed memory|blocked_pending_reviewed_memory_boundary.*no reviewed-memory' docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md README.md`
  - 결과: PASS. stale contradiction 후보가 남아 있지 않았습니다.
- `git diff --check -- README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md work/5/19/2026-05-19-reviewed-memory-shipped-store-wording-residue-docs-bundle.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- 이번 라운드는 docs-only truth reconciliation입니다. 제품 코드, runtime code, tests, Playwright selector, browser UI, storage schema는 변경하지 않았습니다.
- `README.md`와 세 제품 문서는 기존 dirty state가 남아 있는 상태였고, 관련 없는 기존 변경은 되돌리지 않았습니다.
- 전체 unittest, Playwright, `make e2e-test`, controller startup, live runtime start/stop/restart, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았습니다.
- commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
