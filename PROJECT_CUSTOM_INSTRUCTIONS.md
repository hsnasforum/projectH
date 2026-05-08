이 저장소는 **로컬 퍼스트 문서 비서 웹 MVP**입니다. 첫 번째
reviewed-memory slice는 review queue, aggregate apply, active effect,
explicit stop, reversal, conflict visibility까지 출하된 상태입니다.

장기 북극성은 사용자가 교정/승인/거절/예시로 가르칠 수 있는 **학습
준비형 로컬 개인 에이전트**입니다. 하지만 현재 단계는 문서 작업 MVP이며,
프로그램 조작이나 모델 자체 학습을 구현한 상태가 아닙니다.

현재 구현 기준의 중심은 로컬 웹 셸, 최근 세션/타임라인, 파일 요약,
문서 검색, 일반 채팅, 승인 기반 저장, approval reissue, evidence/source
panel, 웹 조사 history, reviewed-memory review queue와 active effect,
Playwright smoke coverage입니다. 이 목록은 제품 방향을 넓히기 위한
마케팅 문구가 아니라 현재 shipped contract를 잊지 않기 위한 요약입니다.

## 1. 항상 작게 읽습니다

- `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`는
  항상 읽는 root memory이므로 중간형 routing/guardrail page로 유지합니다.
- operator boundary, role ownership, publish/merge gate, 기록/검증 필수 조건은
  루트에 남기고, 저수준 runtime 세부사항만 필요할 때 읽습니다.
- 기본 round read set은 active owner root memory 1개, active
  control/work/verify 파일, 실제로 만질 source/test 파일입니다.
- 세부 규칙은 필요할 때만 읽습니다.
  - pipeline/runtime: `.pipeline/README.md`, `.pipeline/harness/*.md`,
    `.claude/rules/pipeline-runtime.md`
  - browser/E2E: `.claude/rules/browser-e2e.md`
  - doc sync: `.claude/rules/doc-sync.md`
  - product truth: `docs/project-brief.md`, `docs/PRODUCT_SPEC.md`,
    `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`,
    `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`
- `work/README.md`, `verify/README.md`, `.pipeline/README.md` 같은 정적 guide는
  매 prompt에 기본 포함하지 말고, 해당 정책이 필요한 경우에만 읽습니다.
- `docs/TASK_BACKLOG.md`, `docs/MILESTONES.md`, `docs/NEXT_STEPS.md`처럼 큰
  계획 문서는 전체 `cat` 대신 targeted search나 필요한 section만 읽습니다.
  그래도 근거가 부족하면 더 넓히지 말고 필요한 exact evidence를 남깁니다.

## 2. 범위를 넓히지 않습니다

- 현재 제품 중심은 `로컬 문서 비서`입니다.
- 웹 조사는 보조 기능입니다.
- 범용 지식 챗봇이나 자율 프로그램 조작으로 조용히 확장하지 않습니다.
- 문서에는 항상 `현재 구현`, `다음 단계`, `장기 북극성`을 분리해 씁니다.
- GPT-5.5 같은 frontier model release는 runtime capability context일 뿐,
  문서-first MVP 범위, 교체 가능한 런타임, 승인/operator 경계를 바꾸지
  않습니다.

## 2.5. Prompt를 outcome-first로 유지합니다

- prompt와 agent rule은 사용자-visible 목표, 성공 기준, 제약, 출력 형태,
  stop rule을 먼저 두고 절차는 필요한 만큼만 둡니다.
- context gathering은 관련 파일이나 근거가 불명확할 때만 넓게 시작하고,
  exact path, contract, check, source evidence가 잡히면 멈춥니다. 검증 실패,
  신호 충돌, material unknown이 있을 때만 focused batch를 한 번 더 돕니다.
- `must`, `never`, `always`, `only` 같은 강한 표현은 approval, 기록, 검증
  정직성, irreversible action처럼 진짜 불변식에만 씁니다.
- long-running/tool-heavy 작업은 중간 진행 업데이트와 final answer를
  분리하고, Responses-style replay에서는 `commentary`와 `final_answer`
  phase 값을 보존합니다.

## 3. 로컬 우선과 승인 안전을 유지합니다

- 기본 동작은 로컬 파일과 로컬 저장을 우선합니다.
- 모델, 런타임, 저장 구조는 교체 가능해야 합니다.
- 특정 공급자나 특정 모델명을 제품 기본값처럼 강제하지 않습니다.
- 파일 저장은 승인 없이 실행하지 않습니다.
- overwrite/delete/move/shell/외부 publish/merge/auth/credential 작업은 위험
  경계입니다.
- 웹 검색은 읽기 전용, 권한 게이트, 로컬 기록 유지 원칙을 따릅니다.
- OCR은 아직 미지원이며 조용히 실패시키지 않습니다.

## 4. 자동화 완성 목표

- 일반적인 next-step, ambiguity, stall, session rollover, recovery 상황에서
  사용자를 호출하지 않는 것이 목표입니다.
- 문제가 생기면 implement / verify-handoff / advisory owner가 `/work`,
  `/verify`, current docs, runtime evidence를 보고 먼저 하나의 다음
  control로 좁힙니다.
- `STATUS: needs_operator`는 destructive/auth/credential/approval-record/
  truth-sync/publication/merge 같은 실제 위험이나 명시 승인 경계에만 남기는
  것이 목표입니다.
- 선택지형 stop이 current docs, milestone, 최신 `/work`, 최신 `/verify`로
  좁혀질 수 있으면 operator에게 바로 묻지 말고 advisory-first로 줄입니다.
- operator stop을 열 때는 `CONTROL_SEQ`, `REASON_CODE`, `OPERATOR_POLICY`,
  `DECISION_CLASS`, `DECISION_REQUIRED`, `BASED_ON_WORK`, `BASED_ON_VERIFY`를
  남겨 왜 멈췄고 무엇을 결정해야 하는지 분명히 합니다.
- 재귀학습은 모델 학습이 아니라 repo-local operational memory입니다.
  `/work`, `/verify`, incident family, replay test, shared helper, runtime
  surface가 다음 판단을 더 작게 만들어야 합니다.

## 5. Single Tmux Runtime 요약

- active role binding이 owner를 정합니다. vendor-named historical filename이
  owner를 정하지 않습니다.
- canonical control slot은 아래 네 개입니다.
  - `.pipeline/implement_handoff.md`
  - `.pipeline/advisory_request.md`
  - `.pipeline/advisory_advice.md`
  - `.pipeline/operator_request.md`
- historical aliases는 read-only compatibility input입니다.
  `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`,
  `.pipeline/gemini_advice.md`
- `.pipeline/harness/*.md`는 role protocol이지 control slot이 아닙니다.
- `.pipeline/session_arbitration_draft.md`는 `STATUS: draft_only`만 담는
  non-canonical draft입니다.
- `.pipeline/codex_feedback.md`와 `.pipeline/gpt_prompt.md`는 optional/legacy
  scratch일 뿐 canonical execution path가 아닙니다.
- newest valid control은 `CONTROL_SEQ` 우선, `mtime` 보조로 판정합니다.
- persistent truth는 `/work`와 `/verify`입니다. `.pipeline`과 충돌하면 최신
  `/work`/`/verify`를 우선합니다.

## 6. 역할 경계

Verify/handoff owner:
- 최신 relevant `/work`와 같은 날짜 `/verify`를 먼저 봅니다.
- 가장 좁은 정직한 검증을 재실행합니다.
- `/verify`를 남기거나 갱신한 뒤 다음 control을 씁니다.
- exact slice가 정해지면 `.pipeline/implement_handoff.md`를 씁니다.
- next-slice ambiguity면 `.pipeline/advisory_request.md`를 먼저 엽니다.
- advisory recovery prompt에 `ADVISORY_FOLLOWUP_ALLOWED: false`가 있으면
  새 `.pipeline/advisory_request.md`를 다시 열지 말고 implement 또는 실제
  operator boundary로 수렴합니다.
- real operator-only decision이나 safety/truth/approval/publication blocker일
  때만 `.pipeline/operator_request.md`를 씁니다.
- active implement-owner session의 context exhaustion, rollover,
  continue-vs-switch 질문은 advisory coordination 뒤 짧은 lane reply로
  돌려보내고, `.pipeline/implement_handoff.md`는 session boundary 전까지
  유지합니다.
- watcher가 operator retriage를 보냈으면 하나의 newer control slot으로
  닫습니다. 아무 control 없이 idle로 돌아가면 watcher가
  `operator_retriage_no_next_control`로 advisory 승격할 수 있습니다.
- 승인된 large-bundle publish follow-up은 verify/handoff owner가 처리하거나
  advisory로 넘깁니다. implement lane에 commit/push/PR 생성을 넘기지
  않습니다.

Implement owner:
- `STATUS: implement`의 exact slice만 구현합니다.
- 다음 slice를 self-select하지 않습니다.
- bounded edits와 canonical `/work` closeout에서 멈춥니다.
- commit, push, branch/PR publish, merge는 하지 않습니다.
- 막히면 pane-local `STATUS: implement_blocked` sentinel을 남기고 verify
  triage로 넘깁니다.
- blocked sentinel은 가능하면 `BLOCK_REASON`, `BLOCK_REASON_CODE`,
  `REQUEST: verify_triage`, `ESCALATION_CLASS: verify_triage`, `HANDOFF`,
  `HANDOFF_SHA`, `BLOCK_ID`를 포함합니다.

Advisory owner:
- 후보를 exact slice 1개, axis switch 1개, 또는 operator decision 1개로
  줄입니다.
- `report/gemini/...md`와 `.pipeline/advisory_advice.md`를 모두 남깁니다.
- 최종 implement/operator slot은 직접 쓰지 않습니다.

Publish/merge 경계:
- ordinary small/local slice는 `/work` closeout과 local dirty state에서
  멈춥니다.
- `commit_push_bundle_authorization + internal_only`와
  `pr_creation_gate + gate_24h + release_gate`는 이미 승인된 큰 묶음
  follow-up일 때 verify/handoff owner가 auditable하게 처리할 수 있습니다.
- `pr_merge_gate`, destructive publication, auth/credential,
  approval-record/truth-sync blocker, external publication boundary는 operator
  승인 경계로 남깁니다.

## 7. 슬라이스 선정

다음 슬라이스는 아래 중 하나를 개선해야 합니다.
- current document-first MVP 사용자 가치
- 현재 shipped flow의 실제 리스크 감소
- 구현-문서 truth mismatch 해소

기본 우선순위:
1. same-family current-risk reduction
2. same-family user-visible improvement
3. new quality axis
4. internal cleanup

Route/helper completeness나 검증 공백만으로 roadmap priority를 올리지
않습니다. 같은 날 same-family docs-only truth-sync가 3회 이상 반복되면 더
작은 docs-only micro-slice가 아니라 bounded bundle 또는 escalation으로
전환합니다.

## 8. 재귀개선

- 먼저 existing incident family인지 new incident family인지 분류합니다.
- 같은 family면 조건문을 더 얹기보다 owning boundary/shared helper/replay를
  강화합니다.
- 새 family면 named incident, focused replay test, truthful runtime surface를
  먼저 남깁니다.
- launcher/controller/browser 같은 thin client에 truth inference를 덧붙여
  runtime drift를 숨기지 않습니다.
- Long soak는 baseline evidence이며, runtime contract가 크게 바뀐 경우가
  아니면 focused replay + live gate를 우선합니다.

## 9. 문서 동기화

- UI 동작이 바뀌면 `README.md`, `docs/PRODUCT_SPEC.md`,
  `docs/ACCEPTANCE_CRITERIA.md`를 확인합니다.
- approval/session/storage schema가 바뀌면 `docs/ARCHITECTURE.md`도 확인합니다.
- 테스트/마일스톤 의미가 바뀌면 `docs/MILESTONES.md`,
  `docs/TASK_BACKLOG.md`도 확인합니다.
- agent/skill/operator config가 바뀌면 `AGENTS.md`, `CLAUDE.md`,
  `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.codex/config.toml`,
  mirrored agent/skill files를 함께 맞춥니다.
- Claude 전용 상세 규칙은 `CLAUDE.md`를 키우지 말고 `.claude/rules/*.md`로
  내립니다.
- 장기 roadmap이나 staged product framing이 바뀌면 `plandoc/`도 확인합니다.
- 새 agent는 반복 workflow나 반복 risk area가 있을 때만 추가합니다.
- 새 skill은 `.agents/skills/`와 `.claude/skills/`에 mirror하고, Codex가
  기본으로 써야 하면 `.codex/config.toml`에도 등록합니다.
- mirrored agent/skill/config 변경은 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
  `PROJECT_CUSTOM_INSTRUCTIONS.md`와 함께 맞춥니다.

권장 wrapper 순서:
- `onboard-lite`는 unfamiliar subsystem orientation
- `finalize-lite`는 implementation-side wrap-up
- `round-handoff`는 verification truth/handoff
- `next-slice-triage`는 truth가 이미 current일 때 exact next slice 선정
- wrapper 하나가 다른 wrapper의 책임까지 먹지 않게 합니다.

## 10. 기록과 검증

- 의미 있는 구현/운영 작업은 `work/<월>/<일>/YYYY-MM-DD-<slug>.md`에
  한국어 closeout을 남깁니다.
- 의미 있는 검증/truth reconciliation은
  `verify/<월>/<일>/YYYY-MM-DD-<slug>.md`에 한국어 note를 남깁니다.
- `.pipeline/` execution slot은 concise English-led instructions를 유지합니다.
- 파일 경로, 테스트 이름, selector, field name, literal identifier는 원문을
  유지합니다.
- closeout에는 `변경 파일`, `사용 skill`, `변경 이유`, `핵심 변경`, `검증`,
  `남은 리스크`를 남기는 편이 맞습니다.
- 검증 전용 메모에서 파일을 바꾸지 않았다면 `변경 파일 - 없음`이라고
  적습니다.
- 검증은 가장 좁은 relevant check부터 시작합니다.
- 실행하지 않은 검증은 미실행으로 솔직하게 남깁니다.

## 11. 응답 방식

- 사용자에게는 한국어 존댓말로 답합니다.
- 사실, 가정, 권고를 구분합니다.
- 구현 전후에는 목표, 영향 파일, 리스크, 검증 결과를 짧게 요약합니다.
