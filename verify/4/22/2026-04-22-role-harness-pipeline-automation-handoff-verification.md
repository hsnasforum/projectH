# 2026-04-22 role harness pipeline automation handoff verification

## 변경 파일
- `verify/4/22/2026-04-22-role-harness-pipeline-automation-handoff-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`: 최신 `/work`를 다시 읽고, 다음 control을 pipeline launcher 자동화 방향으로 고정하기 위해 사용
- `work-log-closeout`: 기존 `/work` closeout의 남은 리스크에 다음 자동화 우선순위 흔적을 보강하기 위해 사용

## 변경 이유
- 현재 `.pipeline/gemini_request.md` CONTROL_SEQ 735는 post-publish next-slice advisory를 열고 있어, 최신 role harness 작업이 pipeline launcher / watcher 자동화 후속으로 이어지지 않을 수 있습니다.
- 오늘 최신 `/work`는 role harness protocol과 supervisor-managed prompt integration을 닫았지만, 같은 날짜 `/verify`가 비어 있어 runtime이 이전 product/publish 맥락을 더 강하게 볼 수 있습니다.
- 따라서 persistent verification truth와 rolling handoff에 "다음은 pipeline launcher 자동화 안정화"라는 방향을 명확히 남깁니다.

## 핵심 변경
- `work/4/22/2026-04-22-role-harness-protocol.md`의 남은 리스크에 다음 우선순위가 pipeline launcher / watcher 자동화 안정화임을 명시했습니다.
- 이 `/verify` note는 최신 role harness round가 코드/문서/테스트 기준으로 닫혔고, 후속은 product milestone work가 아니라 runtime automation current-risk reduction이어야 한다고 기록합니다.
- `.pipeline/claude_handoff.md`는 CONTROL_SEQ 736으로 갱신해, 낮은 seq의 post-publish advisory보다 새로운 implement control이 current truth가 되도록 합니다.
- 다음 implement slice는 하드코딩 금지, 중복 금지, 과도한 단일 파일 책임 집중 금지를 전제로 `gemini_advisory_recovery` / role harness / supervisor prompt integration의 실제 launcher 자동화 경로를 더 단단히 하는 방향입니다.

## 검증
- 최신 `/work`: `work/4/22/2026-04-22-role-harness-protocol.md` 확인.
- 오늘 `/verify`: 기존 파일 없음 확인.
- 현재 rolling controls 확인:
  - `.pipeline/gemini_request.md` CONTROL_SEQ 735는 post-publish next-slice advisory.
  - `.pipeline/claude_handoff.md`는 이전 product smoke drift handoff CONTROL_SEQ 733.
- 변경 후 `parse_control_slots(.pipeline)` 확인:
  - active: `.pipeline/claude_handoff.md` / `STATUS: implement` / `CONTROL_SEQ: 736`
  - stale: `.pipeline/gemini_request.md` seq 735, `.pipeline/operator_request.md` seq 734, `.pipeline/gemini_advice.md` seq 731
- 직전 role harness 검증 결과:
  - `python3 -m py_compile watcher_prompt_assembly.py pipeline_runtime/supervisor.py pipeline_runtime/role_harness.py pipeline_gui/setup_profile.py` 통과.
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_role_harness tests.test_pipeline_gui_setup_profile tests.test_watcher_core.WatcherPromptAssemblyTest tests.test_pipeline_runtime_schema` 통과 (`204 tests`).
  - `git diff --check` 통과.
- 이 verification/handoff 정렬 자체는 코드 변경이 아니므로 추가 unit rerun은 수행하지 않았습니다. `git diff --check`는 재확인했고 통과했습니다.

## 남은 리스크 (CONTROL_SEQ 736 이전)
- `.pipeline/gemini_request.md` CONTROL_SEQ 735는 파일상 남아 있지만, CONTROL_SEQ 736 implement handoff가 더 최신 valid control입니다.
- 이미 실행 중인 live advisory lane이 있다면 pane-local 작업은 남아 있을 수 있습니다. 다음 runtime poll에서 최신 control selection이 CONTROL_SEQ 736을 우선해야 합니다.
- 이번 handoff는 "자동화 방향 고정"입니다. 실제 자동 회의/수렴 강제의 추가 구현은 다음 implement owner가 bounded slice로 처리해야 합니다.

---

## CONTROL_SEQ 736 구현 검증 (NEXT_CONTROL_SEQ: 737)

### 구현된 슬라이스 (CONTROL_SEQ 736 work notes)

1. `work/4/22/2026-04-22-role-bound-lane-routing-cleanup.md`
   - `lane_catalog.py`에 `legacy_watcher_pane_target_arg_for_lane()` 추가, pane 인자 생성이 lane config 순회로 전환
   - live session arbitration snapshot key를 `claude/codex/gemini` → `implement/verify/advisory` role key로 전환
   - `watcher_dispatch.py` pending signal mismatch fallback에 `role_owner()` 우선 사용

2. `work/4/22/2026-04-22-verify-route-label-normalization.md`
   - `pipeline_runtime/role_routes.py` 신규 추가: `verify_followup` / `verify_triage` canonical label + `codex_*` legacy alias 정규화
   - operator autonomy, turn arbitration, supervisor, watcher prompt dispatch를 `verify_*` 계열로 전환
   - implement blocked sentinel과 agent instruction을 `REQUEST: verify_triage`, `ESCALATION_CLASS: verify_triage`로 갱신

3. `work/4/22/2026-04-22-role-based-control-filename-migration.md`
   - `pipeline_runtime/schema.py`에 `ControlSlotSpec` 기반 registry 추가
   - canonical: `implement_handoff.md`, `advisory_request.md`, `advisory_advice.md`, `operator_request.md`
   - legacy alias: `claude_handoff.md`, `gemini_request.md`, `gemini_advice.md`
   - watcher/supervisor/GUI backend, archive helper, agent docs, runtime docs 전면 동기화

### 검증 결과 (NEXT_CONTROL_SEQ: 737, 2026-04-22)

- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py pipeline_runtime/role_routes.py pipeline_runtime/lane_catalog.py watcher_core.py watcher_dispatch.py watcher_prompt_assembly.py` → **통과**
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_watcher_core.WatcherPromptAssemblyTest` → **47 tests, OK**
  - `ROLE_HARNESS: .pipeline/harness/implement.md` (implement prompt) ✅
  - `ROLE_HARNESS: .pipeline/harness/verify.md` + `COUNCIL_HARNESS: .pipeline/harness/council.md` (verify prompt) ✅
  - `ROLE_HARNESS: .pipeline/harness/advisory.md` (advisory prompt) ✅
  - `.pipeline/implement_handoff.md [implement]` verify prompt 포함 ✅
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration` → **138 tests, OK**
  - stale advisory operator fallback, verify prompt slice ambiguity routing 포함 ✅
- `python3 -m unittest tests.test_watcher_core` → **187 tests, OK**
  - `test_stale_gemini_advisory_recovers_to_verify_followup`: ADVISORY_ACTIVE → VERIFY_FOLLOWUP 전환 ✅
  - `test_stale_gemini_advisory_recovery_skips_when_current_advice_exists` ✅
  - `test_gemini_request_idle_retry_redispatches_when_advice_is_stale` ✅
- `git diff --check` → **통과**
- `pipeline_runtime.schema.iter_control_slot_specs()` 실행 확인: 4개 spec 정상 반환 ✅

### 결론

CONTROL_SEQ 736 목표("stalled advisory → one next control without calling operator")는 완전히 충족됨:
- 스테일 advisory recovery → verify owner 자동 dispatch (role harness 포함) ✅
- ROLE_HARNESS / COUNCIL_HARNESS가 verify/recovery prompt에 포함됨 ✅
- 모든 관련 테스트 통과 ✅

### 남은 리스크 (CONTROL_SEQ 736 이후)

- `watcher_core.py` 내 legacy config key `codex_blocked_triage_prompt`: 기존 설정 호환용 read-only alias로 의도적으로 유지됨
- `codex_operator_retriage` notify kind: 입력 alias로만 남김, 출력은 canonical `verify_*` 사용
- 물리 legacy 파일 (`claude_handoff.md`, `gemini_request.md`, `gemini_advice.md`): schema registry가 alias로 처리, 실제 삭제/archive는 후속 slice
- `lane_surface.py` Codex/Gemini activity detector: adapter plane 이름, 이번 cleanup 범위 밖
- `.pipeline/implement_handoff.md` 물리 파일은 CONTROL_SEQ 737 advisory_request 작성이 최초 생성 (이번 round에서 `.pipeline/advisory_request.md`로 쓰므로 아직 physical 존재하지 않음)

### 다음 control

CONTROL_SEQ 737 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: cleanup 잔여 항목 우선순위가 비슷하고(config key alias / physical file archive / lane_surface.py adapter), 방향 전환(product milestone 복귀 여부) 결정이 필요해 advisory-first 적용

---

## CONTROL_SEQ 739 구현 검증 (NEXT_CONTROL_SEQ: 740)

### 검증 대상 work note

`work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`

### 검증 결과

- `watcher_core.py:1497` `config.get("verify_blocked_triage_prompt")` canonical key 존재 확인 ✅
- `watcher_core.py:1499` `config.get("codex_blocked_triage_prompt")` fallback alias 존재 확인 ✅
- `watcher_core.py:1504-1506` sig 변수 `_last_implement_handoff_sig`, `_last_advisory_request_sig`, `_last_advisory_advice_sig` rename 완료 확인 ✅
- 레거시 물리 파일 `claude_handoff.md`, `gemini_request.md`, `gemini_advice.md`: 모두 부재 (`ls` 에러로 확인) ✅
- `python3 -m unittest tests.test_watcher_core` → **191 tests, OK** ✅
- `git diff --check` → 통과, 워크트리 clean ✅

### work note 클레임 진실성 평가

모든 클레임 **truthful**. work note가 명시한 대로, seq 739 handoff의 3가지 항목(config key canonical 추가 / 물리 파일 archive / sig 변수 rename)은 모두 이미 워크트리에 반영된 상태였고, 이번 implement round는 확인 및 archive-script dry-run + legacy 명시 실행만 수행했다.

### 남은 리스크 (CONTROL_SEQ 739 이후)

- `lane_surface.py` Codex/Gemini activity detector 어댑터 이름: 명시적으로 cleanup 범위 밖으로 제외, 선택적 후속 슬라이스
- `.pipeline/archive-stale-control-slots.sh` executable bit 없음: `bash` 호출로 우회 가능, 권한 변경은 seq 739 범위 아님
- `codex_operator_retriage` 입력 alias: 의도적으로 read-only 유지
- `--all-stale` 실행 미완료: canonical advisory/operator slot을 보호하기 위한 올바른 결정이었음
- **infrastructure cleanup family 완료**: advisory (seq 738)가 product milestone 복귀 전 인프라 안정화 완료를 권고했고, 해당 scope의 3개 항목이 모두 확인됨

### 다음 control

CONTROL_SEQ 740 → `.pipeline/advisory_request.md` (STATUS: request_open)
- 이유: 인프라 cleanup family가 scope 기준으로 완료되었고, 다음 방향(product milestone / 구조 4축 owner bundle / 나머지 lane_surface cleanup)이 ambiguous하여 advisory-first 적용
