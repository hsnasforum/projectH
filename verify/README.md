# /verify 정책

`/verify`는 projectH에서 **최신 구현 라운드를 검수**하기 위해 검증 재실행, 현재 truth 재대조, 다음 라운드 handoff 결과를 남기는 verification 디렉터리입니다.

## tracked 대상

- `verify/<month>/<day>/YYYY-MM-DD-<slug>.md` 형식의 verification 메모
- 이 파일처럼 `/verify` 운영 규칙을 설명하는 기준 문서

## 작성 원칙

- 검증 라운드를 시작할 때는 먼저 `work/<현재월>/<현재일>/` 아래의 최신 md 파일을 확인합니다.
- 오늘 `/work` 문서가 없으면 전날 날짜 폴더의 최신 `/work` 문서를 확인하고 이어받습니다.
- 같은 날짜의 `verify/<현재월>/<현재일>/` 아래에 기존 verification 메모가 있으면 그중 최신 파일도 이어서 확인합니다.
- verification 메모를 저장할 때는 `verify/<현재월>/<현재일>/` 폴더가 없으면 먼저 생성합니다.
- 한 verification 라운드가 끝날 때 실제 재실행한 검증, 실제 코드/문서 대조 결과, 현재 truth, 남은 리스크를 한 파일에 정리합니다.
- 기본 모드에서 verification 메모는 "이번 Claude `/work` 주장이 맞는가"를 확인하는 검수 결과서여야 합니다.
- verification 메모는 인위적으로 잘게 쪼갠 micro-round보다, 하나의 의미 있는 bounded slice가 truthfully 닫혔는지 확인하는 단위로 남기는 편이 맞습니다.
- `/verify` verification note는 기본적으로 한국어로 적습니다.
- 다만 파일 경로, 테스트 이름, selector, field name, literal code identifier는 원문을 그대로 유지합니다.
- 새 verification 메모에는 아래 섹션을 이 순서로 둡니다:
  - `## 변경 파일`
  - `## 사용 skill`
  - `## 변경 이유`
  - `## 핵심 변경`
  - `## 검증`
  - `## 남은 리스크`
- `## 사용 skill` 섹션은 항상 두고, 실제 사용한 skill이 없으면 `- 없음`으로 적습니다.
- verification-only 라운드에서 파일을 바꾸지 않았다면 `## 변경 파일`에는 `- 없음`으로 적습니다.
- 실행하지 않은 명령이나 검증 결과를 추측으로 적지 않습니다.

## `/work`와의 경계

- `/work`는 구현 closeout입니다.
- `/verify`는 최신 `/work`에 대한 검수 결과와 truth 재대조 결과입니다.
- 구현이 있었다면 먼저 `/work`가 있고, 그 다음 verification-backed handoff가 의미 있으면 `/verify`가 따라옵니다.
- `/verify`는 `/work`를 대체하지 않습니다. 최신 구현 truth는 항상 최신 `/work`부터 읽고 시작합니다.
- `.pipeline/implement_handoff.md`와 `.pipeline/operator_request.md`는 자동화용 rolling handoff 슬롯이며, 최신 verification truth를 편하게 넘기기 위한 보조 수단일 뿐 `/verify`를 대체하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/advisory_advice.md`는 arbitration용 rolling 슬롯이며, 최신 verification truth를 편하게 넘기기 위한 보조 수단일 뿐 `/verify`를 대체하지 않습니다.
- Historical aliases `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, and `.pipeline/gemini_advice.md` are read-only compatibility inputs for those same role-based slots. They should not be interpreted as separate verification truth or a second control plane.
- `.pipeline` execution/control 슬롯은 `/verify`와 달리 기본적으로 영어 중심 실행 지시를 유지하는 편이 맞습니다.
- canonical control slot은 pending일 때 `CONTROL_SEQ`를 함께 써서 newest-valid-control 판정을 `CONTROL_SEQ` 우선 / `mtime` 보조로 유지하는 편이 맞습니다.
- `.pipeline/session_arbitration_draft.md`는 watcher가 active implement-owner session의 escalation pattern을 감지했고 verify/advisory lanes가 idle이며 implement owner가 idle이거나 짧게 settle된 상태일 때만 남길 수 있는 draft_only 메모이며, 검증 truth나 canonical arbitration 슬롯을 대체하지 않습니다. resolved 조건이 생기면 watcher가 정리할 수 있고, 같은 fingerprint는 짧은 cooldown 동안 반복 생성하지 않습니다.
- `.pipeline/codex_feedback.md`는 optional scratch 또는 legacy compatibility text일 뿐이며, 실행 신호로는 쓰지 않습니다.
- `.pipeline/gpt_prompt.md`는 optional/legacy scratch 슬롯로 남길 수 있지만, canonical single-Codex 흐름의 필수 단계는 아닙니다.
- whole-project trajectory audit이나 milestone-level 평가는 `/verify`가 아니라 `report/`에 남기는 편이 맞습니다.

## 권장 예시

- verification note: `verify/3/30/2026-03-30-reviewed-memory-conflict-source-ref-verification.md`
- reusable same-day template: `verify/3/30/2026-03-30-verification-note-template.md`
- local scratch: `verify/local/<topic>.md`, `verify/local/<topic>.log`

## 운영 메모

- `/verify`는 `/work`와 같은 섹션 순서를 유지하되, 검증자가 실제로 다시 실행한 명령과 현재 truth를 더 엄격하게 기록하는 용도입니다.
- round-handoff, release-check 같은 verification/handoff 성격의 skill을 썼다면 그 사실을 `## 사용 skill`에 적습니다.
- `/work` 또는 `/verify` 정책이 바뀌면 두 README를 같은 라운드에서 함께 갱신해 후속 작업자가 경계를 헷갈리지 않게 합니다.
- single tmux 흐름에서는 active verify/handoff owner가 실제 검증 후 `/verify`를 남긴 다음:
  - 구현 가능한 경우 `.pipeline/implement_handoff.md`에 `STATUS: implement`
  - advisory arbitration이 필요하면 `.pipeline/advisory_request.md`에 `STATUS: request_open`
  - advisory owner가 `.pipeline/advisory_advice.md`에 `STATUS: advice_ready`
  - 멈춰야 하는 경우 `.pipeline/operator_request.md`에 `STATUS: needs_operator`
  를 남깁니다. persistent verification truth는 항상 `/verify`가 먼저입니다.
- 따라서 pane 안 reasoning만 남기거나 next control slot만 먼저 갱신하는 것은 canonical verification closeout이 아닙니다. `/verify`를 먼저 남기거나 갱신한 뒤에만 다음 control slot을 쓰는 편이 맞습니다.
- watcher가 implement-owner pane의 `STATUS: implement_blocked` sentinel을 감지한 경우에도, active verify/handoff owner는 그 blocked triage를 `.pipeline/implement_handoff.md` / `.pipeline/advisory_request.md` / `.pipeline/operator_request.md` 중 하나의 최신 valid control로 닫는 편이 맞습니다. blocked sentinel 자체에는 `BLOCK_REASON_CODE`와 `ESCALATION_CLASS`를 함께 두는 편이 canonical입니다.
- `STATUS: needs_operator`를 쓸 때는 bare stop line만 남기지 말고, 최소한 `CONTROL_SEQ`, `REASON_CODE`, `OPERATOR_POLICY`, `DECISION_CLASS`, `DECISION_REQUIRED`, `BASED_ON_WORK`, `BASED_ON_VERIFY`, stop reason, 근거가 된 latest `/work`와 `/verify`, 그리고 operator가 다음에 무엇을 정해야 하는지를 같이 남깁니다.
- `/verify`의 1차 목적은 현재 truth를 정직하게 다시 맞추는 것입니다. 다음 슬라이스 제안은 가능하지만, 단순한 uncovered regression 채우기보다 현재 MVP 우선순위를 먼저 통과해야 합니다.
- `/verify`의 1차 목적은 repo 전체 상태를 새로 재판정하는 것이 아니라, 최신 implement-owner 라운드가 truthful한지 확인하고 그 범위 안에서 다음 한 슬라이스를 좁게 제안하는 것입니다.
- 다음 슬라이스를 제안할 때도 기존 shared path 재사용으로 중복 코드를 줄일 수 있는지 먼저 보고, 하나의 coherent slice로 닫을 수 있는데도 필요 이상으로 micro-slice로 쪼개지 않습니다.
- latest `/work`와 `/verify`가 한 family를 truthfully 닫았다면, 다음 슬라이스 제안은 보통 같은 family의 가장 작은 current-risk reduction부터 검토하는 편이 맞습니다.
- 자동 제안 우선순위는 보통 다음과 같습니다.
  - same-family current-risk reduction
  - same-family user-visible improvement
  - new quality axis
  - internal cleanup
- 다만 같은 날 same-family docs-only truth-sync가 이미 3회 이상 반복됐다면, `/verify`는 또 하나의 더 작은 docs-only micro-slice를 기본 제안으로 내지 않는 편이 맞습니다. 이 경우 남은 drift를 한 번에 닫는 bounded bundle이나 advisory/operator escalation을 먼저 검토합니다.
- 따라서 `/verify`에서 바로 다음 단일 슬라이스를 고르지 못했다면, implement owner에게 선택권을 넘기지 않습니다.
- 다음 막힘이 next-slice ambiguity, overlapping candidates, low-confidence prioritization이라면 `.pipeline/operator_request.md`보다 `.pipeline/advisory_request.md`를 먼저 열고 Gemini recommendation을 받은 뒤 active verify/handoff owner가 다시 한 번 exact slice를 좁히는 편이 맞습니다.
- 문자/숫자/한글 라벨 선택지형 stop(괄호형 inline 라벨 포함)도 current docs, milestone, 최신 `/work`, 최신 `/verify`로 좁힐 수 있는 문제라면 먼저 Gemini recommendation을 받아 에이전트끼리 줄이고, decision header 자체가 safety/destructive/auth/credential/approval-record/truth-sync blocker일 때만 operator stop을 유지합니다.
- watcher가 operator retriage prompt 이후 verify/handoff lane의 idle return과 no-next-control 상태를 감지해 `operator_retriage_no_next_control`로 `.pipeline/advisory_request.md`를 승격했다면, `/verify`는 그 원 operator slot과 승격된 request를 같이 확인하고 같은 blocker가 반복되지 않는지 검증합니다.
- `.pipeline/operator_request.md`는 real operator-only decision, approval/truth-sync blocker, immediate safety stop, 또는 advisory advice 이후에도 exact slice를 못 좁힌 경우에만 `STATUS: needs_operator`로 남기는 편이 맞습니다.
- commit/push/PR 생성은 release, soak, PR stabilization, direct publish처럼 operator가 명시 승인한 큰 검증 묶음 경계에서만 next action으로 제안합니다. small/local slice의 dirty state만으로 commit/push/PR operator stop을 만들지 않습니다.
- `commit_push_bundle_authorization + internal_only`는 이미 큰 묶음 승인 follow-up이므로 `/verify`는 operator 재호출보다 verify/handoff-owner publish follow-up 또는 완료된 publish의 `operator_approval_completed` recovery를 우선 확인합니다.
- `pr_creation_gate + gate_24h + release_gate`는 draft PR 생성까지 자동 follow-up으로 확인합니다. `/verify`는 PR URL, base/head, 기존 PR 재사용 여부, 실패 시 auth/credential 또는 scope blocker가 `/work`에 남았는지 확인합니다.
- 이 follow-up을 implement handoff로 넘기면 implement lane의 commit/push/PR 금지 규칙과 충돌하므로, verify/handoff owner가 직접 처리하거나 advisory escalation으로 닫는지 확인합니다.
- 자동화 완성 목표는 ordinary next-step, ambiguity, stall, rollover, recovery 상황에서 사용자를 호출하지 않는 것입니다. `/verify`는 에이전트 논의와 evidence로 exact next control을 좁히고, 재귀학습은 incident family/replay/shared helper/runtime surface 같은 repo-local operational memory로 기록합니다.
- `/verify`는 하드코딩된 branch/SHA/seq/pane/prose 의존, near-copy 중복, 한 파일/함수로 과도하게 몰린 책임을 current-risk로 다룹니다. 같은 truth가 반복되면 shared helper나 owning boundary로 올리는 next control을 우선합니다.
- 다만 그 advisory arbitration이 active implement-owner session의 context exhaustion, session rollover, continue-vs-switch 같은 side question을 다루는 경우에는, active verify/handoff owner가 그 답을 implement owner에게 짧은 lane reply로만 relay하고 `.pipeline/implement_handoff.md`는 session boundary 전까지 그대로 두는 편이 맞습니다.
- 다만 그 경우에도 `.pipeline/operator_request.md`는 빈 정지 신호가 아니라, 사람이 다시 읽었을 때 즉시 맥락을 복원할 수 있는 stop handoff여야 합니다.
- focused regression만 다시 돌렸다면 그 이유를 적고, full browser 또는 end-to-end verification을 생략했다면 왜 이번 변경과 직접 관련이 없었는지 분명히 적습니다.
- Playwright-only smoke tightening, selector drift, single-scenario fixture update 같은 브라우저 검수는 isolated scenario rerun을 먼저 적고, `make e2e-test`를 생략했다면 shared browser helper 변경이 없었는지, release/ready 판정 라운드가 아닌지 같이 남기는 편이 맞습니다.
- `route-level`, `handler-level`, `helper-level` completeness 공백은 현재 shipped user flow를 지키는 경우가 아니라면 기본적으로 리스크 메모에 가깝게 다루고, 다음 기능 슬라이스의 자동 기본값으로 승격하지 않습니다.
