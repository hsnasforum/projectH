# 2026-04-21 truth-sync + automation health 완료 후 후속 공정 arbitration

## 핵심 권고 (RECOMMENDATION)

**RECOMMEND: (live restart + C live verify) -> G6 verify note -> commit/push -> 6h soak -> PR**

현재 모든 단위 테스트가 통과(code-green)했으나, 누적된 8회의 SCOPE_VIOLATION으로 인해 작업 트리가 매우 비대하고 복잡합니다. 안정적인 Milestone 5 전환을 위해 "검증 완료 후 베이스라인 고정(commit), 이후 장기 안정성 확인(soak)" 순서를 권장합니다.

## 답변 요약 (SUMMARY)

- **Q1 (C verified): (b) 미충족.** 단위 테스트 PASS는 로직의 정합성을 증명하지만, 이전 라이브 런에서 발생한 집계 누락(0 wrapper events)은 구버전 프로세스 가설 외에도 환경/경로 이슈 가능성이 있습니다. 라이브 재시작을 통한 실측만이 projectH의 실질적 검증 기준을 충족합니다.
- **Q2 (Soak timing): (a) commit/push 먼저 진행.** "PR 전" 요구사항은 최종 게시(Publication) 전의 품질 게이트를 의미합니다. 현재의 비대한 dirty worktree를 그대로 둔 채 6시간 soak를 진행하는 것보다, 검증된 상태를 먼저 커밋하여 복구 가능한 베이스라인을 확보하는 것이 안전합니다.
- **Q3 (G6 note): (a) commit 전 필수.** G6(ENV_BASELINE_ONLY) 종결 노트는 해당 축의 마무리를 증명하는 기록입니다. 모든 변경사항이 하나의 일관된 상태(Atomic commit)로 저장소에 남으려면 커밋 전에 작성이 완료되어야 합니다.
- **Q4 (Sequence):** 라이브 실측 및 G6 서류 정리를 먼저 수행하여 "완전 검증된 상태"를 커밋하고, 이후 가장 시간이 오래 걸리는 6시간 soak를 PR 전 최종 게이트로 배치합니다.

## 판단 근거 (RATIONALE)

1. **라이브 검증의 절대성**: projectH 운영 원칙인 "Validation is the only path to finality"에 따라, 라이브 환경에서의 데이터 집계 확인은 생략할 수 없는 절차입니다.
2. **리스크 관리**: 8회의 SCOPE_VIOLATION이 누적된 상태에서 soak 도중 이슈가 발생할 경우 원인 파악과 롤백이 어렵습니다. 현재 상태를 커밋하여 안정적인 지점을 확보해야 합니다.
3. **일관된 문서화**: G6 결론은 이미 Gemini seq 621에서 합의된 사항입니다. 이를 명문화하여 기술 부채를 정리하고 Milestone 5로 넘어가는 것이 타당합니다.

## 차기 액션 (NEXT ACTION)

- **NEXT_IMPLEMENT**: skip (operator/verify lane이 라이브 재시작 및 G6 노트 종결 수행)
- **NEEDS_OPERATOR**: Decision B (branch commit) 및 Decision C (6h soak 실행 승인)
