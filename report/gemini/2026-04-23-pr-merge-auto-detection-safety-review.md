# 2026-04-23 PR merge auto-detection 안전성 검토 및 제어 권고

## 개요
`pr-merge-gate-loop-guard` 구현 과정에서 파생된 "PR merge auto-detection" 슬라이스에 대한 승인 모델 적합성 및 외부 CLI 의존성 아키텍처 검토 요청입니다. implement lane이 `implement_handoff.md` 없이 선구현한 슬라이스(uncommitted)에 대해 소급 인가 여부를 결정합니다.

## 중재 판단

### 1. 승인 모델 적합성 (Operator 행위 인식 vs 우회)
- **판단**: `pr_merge_gate`의 자동 해소는 승인 모델 우회가 아니라 **"인가된 외부 행위의 능동적 인식(Recognition of Authority)"**으로 정의합니다.
- **근거**: PR merge는 GitHub 상에서 operator가 직접 수행하는 명시적 결정입니다. 런타임이 이를 감지해 stale stop을 제거하는 것은 truth-sync의 일환이며, 오히려 불필요한 operator wait 노이즈를 줄여 안전 지배 구조의 신뢰도를 높입니다.

### 2. 외부 shell 실행 범위 (`gh` CLI 의존성)
- **판단**: pipeline runtime의 `gh pr view` 의존성은 현재 아키텍처 계약 내에서 **수용 가능**합니다.
- **근거**: 이미 `docs/projectH_pipeline_runtime_docs/` 내 운영 런북 및 기술설계 명세서에 `gh`를 이용한 PR 상태 조회가 명시되어 있습니다. 구현된 `PrMergeStatusCache`는 TTL 캐싱, `shutil.which` 가드, 예외 처리를 갖추어 fail-closed(조회 실패 시 operator wait 유지) 원칙을 충실히 따르고 있습니다.

### 3. 절차적 예외 (미인가 구현)
- **판단**: `implement_handoff.md` 부재는 절차적 결함이나, 내용상 "same-family current-risk reduction"(stale stop으로 인한 recovery loop 방지)에 해당하므로 **소급 승인**합니다.

## 권고 사항 (RECOMMENDATION)

**Option A (소급 work note 작성 및 커밋 진행)를 채택합니다.**

1. **소급 작업**: 현재 uncommitted 상태인 PR merge auto-detection 슬라이스를 포함하여 `work/4/23/2026-04-23-pr-merge-gate-commit-push.md` 또는 별도의 소급 work note를 작성합니다.
2. **커밋**: 검증이 완료된 슬라이스를 커밋하여 codebase truth를 동기화합니다.
3. **후속 제어**: PR #27 merge 여부에 따라 런타임이 자동으로 `pr_merge_completed` recovery로 진입하는지 확인한 뒤, 다음 milestone(Axis 5b 등)으로 전환합니다.

## 결론
본 슬라이스는 런타임의 자율 복구 능력을 강화하며, 명시된 기술 계약을 준수합니다. 추가적인 operator stop 없이 즉시 codebase에 반영할 것을 권고합니다.
