# 2026-04-30 M114 다음 아크 방향 권고 — 인프라 및 PR 정리

## 상황 요약
- Review Queue UX 강화 아크(M110–M113)가 검색, 카운트, 배지, 인라인 액션 기능을 모두 갖추며 성공적으로 완결됨.
- 현재 PR 스택이 16개(#91–#106)로 누적되었으며, 모두 draft 상태로 `pr_merge_gate`를 대기 중임.
- 세션이 길어짐에 따라 컨텍스트 소모와 긴 stacked PR 체인으로 인한 기술적 위험(리베이스 복잡도, 잠재적 충돌)이 증가함.

## 판단 근거
- **리스크 감소 (Priority 1)**: `GEMINI.md`의 최우선 순위인 "same-family current-risk reduction"에 따라, 16단계의 unmerged PR 체인을 더 확장하기보다 현재 시점에서 정리하는 것이 가장 중요함.
- **논리적 분기점**: Review Queue UX라는 하나의 큰 기능군이 완성되었으므로, 다음 기능 아크(cross-session memory 등)로 넘어가기 전에 현재까지의 성과를 main에 병합하고 베이스를 안정화하는 것이 적절함.
- **운영 효율성**: PR이 더 쌓일수록 `pr_merge_gate` 승인에 필요한 검토 부하가 기하급수적으로 늘어남.

## 권고 사항
`RECOMMEND: needs_operator D) 인프라 개선 — PR merge 백로그 정리 (#91–#106)`
- **이유**: 현재의 16단계 stacked PR 체인은 시스템의 회복탄력성을 저해하는 리스크 요소임. 다음 기능 아크를 시작하기 전에 PR #91–#106에 대한 `pr_merge_gate` 승인 및 병합을 통해 베이스라인을 안정화할 것을 강력히 권고함.

## 첫 번째 슬라이스 제안 (D 선택 시)
- **Step 1 (Operator)**: PR #91–#106에 대한 순차적 검토 및 병합 (또는 squash merge bundle 처리).
- **Step 2 (Infrastructure)**: 병합 완료 후 로컬 및 원격 브랜치 정리, `feat/` 베이스 최신화.
- **Step 3 (Verification)**: 병합된 최종 상태에서 전체 `make e2e-test` 및 `make test`를 통한 통합 검증.
