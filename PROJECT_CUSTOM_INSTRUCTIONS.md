이 저장소는 **로컬 퍼스트 문서 비서 웹 MVP**이며, 첫 번째 reviewed-memory slice (review queue `검토 후보`, aggregate apply trigger `검토 메모 적용 후보`, emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility)가 출하되어 있습니다.

다만 장기 북극성은 단순 문서 비서가 아니라, 사용자가 하나씩 가르치고 나중에는 프로그램 조작까지 확장할 수 있는 **학습 준비형 로컬 개인 에이전트**입니다.
현재 단계는 그 장기 목표를 위한 첫 단계이며, 아직 프로그램 조작이나 모델 자체 학습을 구현한 상태는 아닙니다.

현재 구현 기준의 중심은 아래입니다.
- 로컬 웹 셸
- 최근 세션 / 타임라인
- 파일 요약 / 문서 검색 / 일반 채팅
- 승인 기반 저장
- approval 재발급(reissue) 흐름
- 근거/출처 패널 (source-role trust labels 포함)
- structured search result preview panel
- summary source-type labels (`문서 요약` / `선택 결과 요약`)
- 요약 반영 구간 패널 (summary span / applied-range)
- response origin badge with separate answer-mode badge for web investigation, source-role trust labels, and verification strength tags in origin detail
- applied-preferences badge (`선호 N건 반영`)
- 스트리밍 진행 표시와 취소
- 응답 피드백 수집
- grounded-brief artifact trace anchor, original-response snapshot, corrected-outcome capture, corrected-save bridge, and artifact-linked reject/reissue reason traces
- PDF text-layer 읽기와 OCR 미지원 안내
- 권한 게이트 기반 웹 조사 (disabled/approval/enabled per session) with local JSON history, in-session reload, and history-card badges (answer-mode badges, color-coded verification-strength badges, color-coded source-role trust badges)
- entity-card / latest-update answer-mode distinction with separate verification labels and entity-card strong-badge downgrade
- claim-coverage panel with status tags, actionable hints, source role with trust level labels, color-coded fact-strength summary bar, and dedicated plain-language focus-slot reinvestigation explanation (reinforced / regressed / still single-source / still unresolved)
- review queue (`검토 후보`), aggregate apply trigger (`검토 메모 적용 후보`), emitted/apply/result/active-effect path, stop-apply, reversal, and conflict-visibility
- Playwright 스모크 검증

항상 아래 원칙을 따르세요.

## 1. 범위를 함부로 넓히지 않습니다
- 현재 제품의 중심은 `로컬 문서 비서`입니다.
- 웹 검색은 보조 조사 기능입니다.
- 범용 지식 챗봇 경쟁처럼 범위를 넓히지 않습니다.
- 장기 목표가 개인 에이전트라고 해도, 현재 단계 문서에서는 `현재 구현`과 `장기 목표`를 반드시 분리해서 씁니다.

## 2. 로컬 우선 원칙을 유지합니다
- 기본 동작은 로컬 파일과 로컬 저장을 우선합니다.
- 모델, 런타임, 저장 구조는 교체 가능하게 유지합니다.
- 특정 공급자나 특정 모델명을 제품 기본값처럼 강제하지 않습니다.
- 사용자의 교정, 승인, 선호 정보가 나중에 개인화 자산이 될 수 있도록 구조화 가능성을 열어 둡니다.

## 3. 안전성을 우선합니다
- 파일 저장은 승인 없이 실행하지 않습니다.
- overwrite / delete / move / shell 실행 / 외부 네트워크는 위험 작업입니다.
- 웹 검색은 읽기 전용 + 권한 게이트 + 로컬 기록 유지 원칙을 지킵니다.
- OCR은 아직 미지원이며, 조용히 실패시키지 않습니다.
- 장기적으로 프로그램 조작을 하더라도 승인, 감사 가능성, 가시성 없는 자동 행동은 허용하지 않습니다.

## 4. 문서와 구현을 같이 유지합니다
- UI 동작이 바뀌면 `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ACCEPTANCE_CRITERIA.md`를 같이 봅니다.
- approval payload나 session schema가 바뀌면 `docs/ARCHITECTURE.md`도 같이 갱신합니다.
- 테스트 시나리오가 바뀌면 `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`도 같이 맞춥니다.
- 에이전트/스킬 설정이 바뀌면 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `.codex/config.toml`, 대응되는 agent/skill 파일을 같이 맞춥니다.
- `/work` closeout 규칙이나 `/verify` verification 규칙이 바뀌면 `work/README.md`, `verify/README.md`도 같이 갱신합니다.
- `.pipeline/gpt_prompt.md`, `.pipeline/codex_feedback.md` 같은 rolling handoff 슬롯 규칙이 바뀌면 `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `PROJECT_CUSTOM_INSTRUCTIONS.md`, `work/README.md`, `verify/README.md`, 필요 시 `.pipeline/README.md`도 같이 갱신합니다.
- 장기 로드맵이나 단계 정의가 바뀌면 `plandoc/` 문서도 같이 맞춥니다.

## 5. 운영 보조 에이전트와 스킬도 제품 범위를 따라갑니다
- 새 agent는 반복적으로 발생하는 저장소 리스크나 워크플로우에만 추가합니다.
- 현재 저장소에서 특히 가치가 큰 역할은 `planner`, `reviewer`, `spec-editor`, `qa-e2e-reviewer`, `approval-auditor`, `investigation-reviewer`, `documenter`, `trace-implementer`입니다.
- 새 skill은 `.agents/skills/`와 `.claude/skills/`에 거울처럼 유지하고, Codex 기본 사용 대상이면 `.codex/config.toml`에도 등록합니다.
- 웹 조사 품질, 승인 플로우, 문서 동기화, `/work` closeout처럼 현재 저장소의 실제 문제 축에 맞는 skill을 우선합니다.
- 최신 `/work` closeout 재검증과 다음 라운드 지시사항 작성처럼 반복되는 handoff 정리는 `round-handoff` 같은 좁은 skill로 표준화하고, 기존 `documenter` 역할과 중복되는 새 agent는 쉽게 늘리지 않습니다.
- 장기 방향을 다루는 planning 계열 문서는 “지금 구현된 것”과 “장기 북극성”을 섞지 않게 설계합니다.
- `trace-implementer`는 grounded-brief trace anchor, snapshot normalization, corrected-outcome linkage 같은 작은 구현 슬라이스를 맡기되, review queue나 user-level memory 같은 다음 단계 범위를 끌어오지 않도록 제한합니다.
- 구현이나 제안 전에 기존 shared helper, query, formatter, prompt가 있는지 먼저 보고, 같은 책임의 near-copy 코드를 새로 늘리지 않습니다.
- 작업은 필요 이상으로 잘게 쪼개지 않습니다. 같은 파일과 같은 검증 경로를 공유하는 변경은 review 가능한 범위 안에서 하나의 의미 있는 슬라이스로 묶습니다.

## 6. `/work` / `/verify` 작업기록 규칙
- 의미 있는 구현/운영 작업이 끝나면 `work/<월>/<일>/YYYY-MM-DD-<slug>.md` 형식으로 closeout 메모를 남깁니다.
- 의미 있는 검증 재실행 / truth 재대조 / 다음 라운드 handoff 작업이 끝나면 `verify/<월>/<일>/YYYY-MM-DD-<slug>.md` 형식으로 verification 메모를 남깁니다.
- `work/`, `verify/`, `report/` 같은 persistent 기록은 기본적으로 한국어로 남깁니다.
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `.pipeline/operator_request.md` 같은 execution/control 슬롯은 기본적으로 영어 중심 실행 지시로 유지합니다.
- 다만 파일 경로, 테스트 이름, selector, field name, literal code identifier는 기록 언어와 무관하게 원문 그대로 둡니다.
- `.pipeline/claude_handoff.md`는 현재 Claude 실행용 rolling 최신 슬롯입니다.
- `.pipeline/gemini_request.md`는 현재 Codex -> Gemini arbitration 요청 슬롯입니다.
- `.pipeline/gemini_advice.md`는 현재 Gemini -> Codex advisory 슬롯입니다.
- `.pipeline/operator_request.md`는 현재 operator 정지용 rolling 최신 슬롯입니다.
- `.pipeline/session_arbitration_draft.md`는 watcher가 active session side-question을 감지했을 때 Codex/Gemini가 idle이고 Claude가 idle이거나 같은 escalation text에 짧게 안정돼 있을 때만 남길 수 있는 non-canonical draft 슬롯입니다. Claude activity resume, canonical Gemini/operator open 같은 resolved 조건이 생기면 watcher가 다시 정리하고, 같은 fingerprint는 짧은 cooldown 동안 바로 재생성하지 않는 편이 맞습니다.
- Gemini advisory 출력은 shell heredoc/redirection보다 file edit/write tool을 우선 사용합니다.
- Gemini arbitration prompt는 일반 경로 나열보다 `@path` file mention과 exact output path를 우선 사용합니다.
- `.pipeline/codex_feedback.md`는 optional scratch 또는 legacy compatibility text일 뿐이며, 실행 경로나 `/work`와 `/verify`를 대체하지 않습니다.
- `.pipeline/gpt_prompt.md`는 optional/legacy scratch 슬롯로 남길 수 있지만 canonical single-Codex 흐름의 필수 단계는 아닙니다.
- 새 라운드를 시작할 때는 오늘 폴더의 최신 메모를 먼저 보고, 없으면 전날 최신 메모를 이어받습니다.
- 검증 라운드를 시작할 때는 최신 `/work` 메모를 먼저 보고, 같은 날짜의 `/verify` 메모가 있으면 그 다음에 이어받습니다.
- 메모에는 최소한 `변경 파일`, `사용 skill`, `변경 이유`, `핵심 변경`, `검증`, `남은 리스크`를 넣습니다.
- 검증 전용 메모에서 파일을 바꾸지 않았다면 `변경 파일`에는 `- 없음`이라고 적습니다.
- 실행하지 않은 검증은 적지 말고, 미실행이면 그대로 남깁니다.

## 6-1. single Codex tmux 운영 규칙
- Codex는 하나의 verification + handoff 레인입니다.
- 권장 흐름은 아래와 같습니다.
  - Claude가 구현 후 `/work`를 남깁니다.
  - Codex가 최신 `/work`, 최신 `/verify`를 읽고 실제 검증을 재실행합니다.
  - Codex가 `/verify`를 남기거나 갱신합니다.
  - Codex가 다음 Claude 실행용 지시사항을 `.pipeline/claude_handoff.md`에 씁니다.
  - exact slice를 못 좁히면 Codex가 `.pipeline/gemini_request.md`를 씁니다.
  - Gemini가 `.pipeline/gemini_advice.md`와 `report/gemini/...md`를 남깁니다.
  - Codex가 Gemini advice를 읽고 최종 `.pipeline/claude_handoff.md` 또는 `.pipeline/operator_request.md`를 씁니다.
  - operator 결론이 필요하면 `.pipeline/operator_request.md`를 씁니다.
- 다만 Claude가 이미 active session 안에서 context exhaustion, session rollover, continue-vs-switch 같은 live side question을 던진 경우에는 Codex가 Gemini advice를 짧은 lane reply로만 relay하고, `.pipeline/claude_handoff.md`는 그 세션이 끝날 때까지 다시 쓰지 않는 편이 맞습니다.
- `.pipeline/claude_handoff.md`는 `STATUS: implement`만 담는 실행 슬롯입니다.
- `.pipeline/gemini_request.md`는 `STATUS: request_open`만 담는 arbitration 요청 슬롯입니다.
- `.pipeline/gemini_advice.md`는 `STATUS: advice_ready`만 담는 advisory 슬롯입니다.
- `.pipeline/operator_request.md`는 `STATUS: needs_operator`만 담는 stop 슬롯입니다.
- 위 canonical control slot은 pending일 때 `CONTROL_SEQ`도 함께 써서 newest-valid-control 판정을 `CONTROL_SEQ` 우선, `mtime` 보조로 맞춥니다.
- `.pipeline/session_arbitration_draft.md`는 `STATUS: draft_only`만 담는 draft 슬롯이며, stop/go 실행 신호가 아닙니다.
- `STATUS: implement`이면 Codex가 이미 다음 단일 슬라이스를 확정한 상태이고, Claude는 그 한 슬라이스만 구현합니다.
- Claude 구현 라운드는 bounded 파일 수정과 canonical `/work` closeout에서 끝납니다. implement lane에서 commit, push, branch publish, PR 생성까지 진행하지 않습니다.
- 그 handoff가 막혔으면 Claude는 operator 선택지를 새로 열지 말고, pane 출력에만 `STATUS: implement_blocked` + `BLOCK_REASON` + `REQUEST: codex_triage` + `HANDOFF` + `HANDOFF_SHA` + `BLOCK_ID`를 남긴 뒤 멈춥니다.
- `STATUS: needs_operator`이면 Codex가 아직 truthful하게 다음 단일 슬라이스를 확정하지 못한 상태이며, Claude는 새 구현을 시작하지 않고 대기합니다.
- `STATUS: needs_operator`는 한 줄짜리 bare stop signal로 끝내지 않습니다. 최소한 아래를 같이 남깁니다.
  - 왜 지금 자동 진행을 멈추는지
  - 어떤 최신 `/work`와 `/verify`를 근거로 멈췄는지
  - operator가 무엇을 정하면 다시 구현 가능한 상태로 돌아갈 수 있는지
- 자동화 기준으로는 최신 control 파일과 `STATUS`가 stop/go 제어 신호입니다. 멈추고 싶으면 본문 설명을 조금 바꾸는 대신 stop 슬롯을 최신으로 갱신해야 합니다.
- watcher는 "존재하는 아무 control 파일"이 아니라 `CONTROL_SEQ` 우선 / `mtime` 보조 기준의 최신 valid control만 active로 보고, 더 오래된 stale control file은 dispatch 판단에서 제외합니다.
- `.pipeline/gpt_prompt.md`는 필요하면 scratch나 legacy 호환용으로 남길 수 있지만, canonical 흐름의 필수 단계는 아닙니다.
- rolling 슬롯 파일은 매 라운드 덮어써도 되지만, 영속 truth는 항상 `/work`와 `/verify`에 남겨야 합니다.
- 기본 모드에서 Codex는 "이번 Claude 작업 검수자 + 방향 가드"입니다. 매 라운드 전체 프로젝트 감사처럼 동작하지 않습니다.
- Codex는 검수 후 다음 단일 슬라이스를 정하거나 `needs_operator`로 멈춰야 합니다. "슬라이스가 안 보이면 Claude가 알아서 고르라"는 식으로 넘기지 않습니다.
- Claude는 `.pipeline/operator_request.md`를 구현 입력으로 읽지 않습니다. watcher도 이 stop 슬롯을 Claude에게 전달하지 않습니다.
- Claude는 `.pipeline/gemini_request.md`와 `.pipeline/gemini_advice.md`도 구현 입력으로 읽지 않습니다.
- Claude는 implement lane에서 operator에게 선택지를 직접 묻지 않습니다. 막히면 watcher가 Codex triage로 자동 전이하는 `implement_blocked` sentinel만 남깁니다.
- Gemini는 advisory only입니다. 최종 execution slot이나 operator stop slot은 여전히 Codex가 씁니다.
- Gemini advisory round는 pane-only 답변으로 닫히지 않습니다. `report/gemini/...md`와 `.pipeline/gemini_advice.md`를 둘 다 남겨야 advisory round가 완료된 것으로 봅니다.
- Codex verification round도 pane-only reasoning이나 control-slot rewrite만으로 닫지 않습니다. `/verify`를 먼저 남기거나 갱신한 뒤 다음 control slot을 씁니다.
- 따라서 active Claude session의 side-question arbitration은 `Claude -> Codex -> Gemini -> Codex -> Claude short reply`로 닫고, `.pipeline/claude_handoff.md`는 session boundary 또는 next round handoff에서만 갱신합니다.
- watcher가 이런 side-question을 감지해도 canonical `.pipeline/gemini_request.md`를 자동 생성하지 않습니다. 대신 Codex/Gemini가 idle이고 Claude가 idle이거나 짧게 settle된 상태일 때 `.pipeline/session_arbitration_draft.md`까지만 자동 생성할 수 있고, Codex가 직접 승격 여부를 판단합니다.
- watcher는 파일 감지와 pane 전달까지만 보장합니다. pane이 바쁘거나 interrupted 상태인 경우 자동 전송 후 실제 처리 실패는 watcher 밖의 세션 상태 문제로 봅니다.
- 전체 프로젝트 진단이나 milestone audit이 필요할 때만 별도 `report/` 문서로 분리합니다.

## 6-2. 검증 범위 최소화 원칙
- 검증은 항상 가장 좁은 relevant 범위부터 시작합니다.
- 작은 helper, service, storage, handler 변경은 관련 Python compile + 관련 unittest까지만 우선 수행합니다.
- Playwright-only smoke tightening, selector drift, single-scenario fixture update는 먼저 isolated scenario rerun으로 닫는 편이 맞습니다.
- browser contract를 직접 바꾸지 않았다면 `make e2e-test`를 기본값처럼 반복하지 않습니다.
- `make e2e-test`는 아래 상황에서만 우선순위를 높입니다.
  - 실제 브라우저 UI나 flow가 바뀐 경우
  - browser smoke failure가 현재 blocker인 경우
  - release 또는 ready 판정을 해야 하는 경우
  - shared browser helper나 여러 browser scenario를 함께 건드린 경우
  - isolated browser rerun에서 broader drift 신호가 나온 경우
- 검증 공백이 있다는 사실만으로 다음 슬라이스를 route-by-route completeness 작업으로 확장하지 않습니다.

## 6-3. 다음 슬라이스 선정 원칙
- 다음 슬라이스는 현재 document-first MVP 사용자 가치에 직접 닿아야 합니다.
- 다음 슬라이스 후보는 아래 우선순위로 평가합니다.
  - 사용자가 직접 체감하는 기능 개선
  - 현재 shipped flow의 실제 리스크 감소
  - 문서-코드 truth mismatch 해소
  - 내부 completeness
- 내부 contract, helper, route, handler의 completeness는 기본 우선순위가 아닙니다.
- reviewed-memory 작업도 계속 가능하지만, 다음 슬라이스는 user-visible reviewed-memory clarity, actual document workflow improvement, approval/evidence/search/summary quality 중 무엇을 직접 개선하는지 먼저 설명할 수 있어야 합니다.
- 현재 planning anchor는 reviewed-memory가 사용자에게 보이고, effect가 활성화되며, 사용자가 그 effect를 명시적으로 중단할 수 있는 지점까지입니다. 그 이후 deeper reversal, conflict-visibility, route-by-route completeness는 자동 기본값으로 이어지지 않습니다.
- `/verify`는 이 다음 슬라이스를 제안할 수 있지만, 그 제안은 "이번 Claude 작업 검수 결과"에서 자연스럽게 이어지는 범위여야 하며, 별도 요청 없는 전체 roadmap 재설계로 확장되면 안 됩니다.
- 같은 family를 truthfully 닫은 직후라면, Codex는 다음 슬라이스를 아래 순서로 자동 선택하는 편이 맞습니다.
  - 같은 family의 가장 작은 current-risk reduction
  - 같은 family의 가장 작은 user-visible improvement
  - 그 다음 새로운 quality axis
  - 마지막으로 internal cleanup
- 다만 같은 날 same-family docs-only truth-sync가 이미 3회 이상 반복됐다면, Codex는 더 작은 docs-only micro-slice를 자동 생성하지 말고 남은 drift를 한 번에 닫는 bounded bundle이나 Gemini/operator escalation으로 전환하는 편이 맞습니다.
- `STATUS: needs_operator`는 위 순서로도 한 후보를 truthful하게 못 고를 때나, approval-record / truth-sync 문제가 새 구현보다 먼저일 때만 사용합니다.
- 따라서 stop/go 실행 신호는 `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `.pipeline/operator_request.md`에서만 읽습니다. `.pipeline/codex_feedback.md`는 optional scratch로만 남길 수 있습니다.
- 다만 `STATUS: needs_operator`로 멈출 때도, operator가 다음 결정을 내릴 수 있도록 최소한의 stop reason과 next decision context를 남겨야 합니다.

## 7. 제품 방향 정리 원칙
- 현재 단계의 핵심은 `문서 작업`입니다.
- 다음 단계의 핵심은 `교정/승인/선호를 구조적으로 저장해 다음 답변에 반영하는 것`입니다.
- 장기 단계의 핵심은 `승인 기반 로컬 행동과 프로그램 조작`입니다.
- 그 이후에야 `개인화된 독자 모델` 또는 그에 준하는 적응형 로컬 모델이 의미가 생깁니다.
- 따라서 기획 문서에는 항상 `현재 단계`, `다음 단계`, `장기 단계`를 나눠 적습니다.

## 8. 응답 방식
- 사용자에게는 한국어 존댓말로 답합니다.
- 사실, 가정, 권고를 구분합니다.
- 구현 전/후에는 목표, 영향 파일, 리스크, 검증 결과를 짧게 요약합니다.
