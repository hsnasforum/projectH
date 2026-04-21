# 2026-04-20 dispatch selection monotonic replay verification

## 변경 파일
- `verify/4/20/2026-04-20-dispatch-selection-monotonic-replay-verification.md`

## 사용 skill
- `round-handoff`: seq 543 `.pipeline/claude_handoff.md`(seq 542 `handoff_date_key_mismatch` block recovery; Gemini 541 intent + seq 540 unit-test framing) 구현 주장을 실제 HEAD 상태에 대조하고, handoff 가 요구한 narrowest 재검증(`py_compile` 동등, 신규 타깃 메서드 재실행, `-k build_artifacts` 4 subset 재실행, full supervisor suite, `git diff --check`)을 직접 재실행했습니다.

## 변경 이유
- seq 542 handoff 가 date_key 추출을 `event["payload"]["latest_work"][:10]` 로 작성했지만 seq 533 `_build_artifacts` emit payload 의 `latest_work` 는 `<month>/<day>/<filename>.md` 전체 rel 경로이므로 `"4/18/2026-"` 만 잘려 `"2026-04-18"` 어서션과 영구 미스매치였습니다. Codex sentinel `handoff_date_key_mismatch` 가 이를 정확히 catch 했습니다.
- seq 543 handoff 는 같은 AXIS-OBSERVE-EVALUATE 축을 유지한 채 단 한 줄의 수식 오류만 `Path(event["payload"]["latest_work"]).name[:10]` 로 교체해 seq 530 `candidate.name[:10]` semantic 과 일치하도록 했고, 새 focused replay test 를 `tests/test_pipeline_runtime_supervisor.py` 에 append 하는 것이 목적이었습니다.

## 핵심 변경
- `tests/test_pipeline_runtime_supervisor.py:344-386` 신규 메서드 `test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`
  - 위치: `test_build_artifacts_emits_dispatch_selection_event` (`:305`, seq 533 sibling) 직후, `test_write_status_emits_receipt_and_control_block` (`:388` 이전, seq 539 fixture) 앞. /work 가 기록한 실제 dirty-worktree 기반 placement (seq 543 handoff 가 가리킨 `:290`/`:292` 은 seq 542 시점 기준; 현재 worktree 에는 앞부분에 다른 테스트가 끼어들어 +54 행 shift).
  - fixture: `root/work/4/18/2026-04-18-older-round.md` 먼저 생성 + `_build_artifacts()` 호출, 이어서 `root/work/4/20/2026-04-20-newer-round.md` 생성 + `os.utime` 으로 older_mtime − 100 초로 spoof (newer-date 노트가 mtime 이 더 작음) + `_build_artifacts()` 재호출.
  - 어서션: `first["latest_work"]["path"] == "4/18/2026-04-18-older-round.md"` + `second["latest_work"]["path"] == "4/20/2026-04-20-newer-round.md"` + `supervisor.events_path` JSONL 에서 `dispatch_selection` 이벤트 2개 수집 후 `date_keys = [Path(event["payload"]["latest_work"]).name[:10] for ...]` 로 추출 → `len(dispatch_events) == 2`, `date_keys == ["2026-04-18", "2026-04-20"]`, `date_keys == sorted(date_keys)` 세 건.
  - `:377` 의 `Path(event["payload"]["latest_work"]).name[:10]` 정확 1 건; seq 542 의 buggy `event["payload"]["latest_work"][:10]` 는 파일 전체에서 0건 — handoff recovery 의 positive/negative 확인 모두 통과.
- seq 533 sibling `test_build_artifacts_emits_dispatch_selection_event` (`:305`), seq 536 fixture `test_build_artifacts_uses_canonical_round_notes_only` (`:204` 기준), seq 539 두 fixture (`:450`, `:1308` 기준 `"Based on \`work/4/11/work-note.md\`\n"` 문자열) 모두 byte-for-byte 유지 확인.
- 이번 라운드 편집 없는 파일 재확인: `pipeline_runtime/supervisor.py`, `pipeline_runtime/schema.py`, `watcher_core.py`, `verify_fsm.py`, `scripts/pipeline_runtime_gate.py`, `storage/sqlite_store.py`, `.pipeline/operator_request.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`, `tests/test_pipeline_runtime_schema.py`, `tests/test_watcher_core.py`, `tests/test_operator_request_schema.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_smoke.py`.
- `pipeline_runtime/schema.py:22-25` pre-existing dirty label-rename 유지. seq 527 `latest_verify_note_for_work`, seq 530 `latest_round_markdown`, seq 533 `_build_artifacts` `dispatch_selection` (`pipeline_runtime/supervisor.py:864` 로 shift 되었음; /work 기록 정합), seq 536 + seq 539 fixtures 계약은 byte-for-byte 보존.
- 기존 `eval/` 디렉터리는 이번 라운드 이전에 이미 존재 (`__init__.py`, `harness.py`, `metrics.py`, `report.py`, `scenarios.py`, `results/`). 이번 라운드에서 `eval/dispatcher_integrity.py` 는 만들지 않았고 `eval/` 디렉터리 자체도 건드리지 않음 — Gemini 541 의 artifact-form drift 를 수용하지 않은 점이 이로써 확인.
- seq 542 block (HANDOFF_SHA `6c8d6a9ab12d9f5da3db396c40631f1fadc5a4e0ea107e612571f78e2403dbcd`, BLOCK_REASON_CODE `handoff_date_key_mismatch`, BLOCK_ID `6b52939b01f0723bb4a022c5111b62d395da336b` / `6c8d6a9ab...:handoff_date_key_mismatch`) 은 이번 seq 543 recovery 로 closed.
- `.pipeline` rolling slot snapshot (검증 시각)
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `543` — shipped, 소비 완료.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `540` — advice 541로 응답되어 stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `541` — seq 542→543 chain 에서 intent 부분만 소비되어 stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `521` — canonical literals 보존.

## 검증
- 직접 코드 Read 대조 (`:344-386` 메서드 body 전체 확인; `:377` 에 handoff 가 요구한 `Path(event["payload"]["latest_work"]).name[:10]` 정확히 위치).
- grep 교차 확인:
  - `Path\(event\["payload"\]\["latest_work"\]\)\.name\[:10\]` `tests/test_pipeline_runtime_supervisor.py` 1건 (`:377`) — positive 확인.
  - `event\["payload"\]\["latest_work"\]\[:10\]` `tests/test_pipeline_runtime_supervisor.py` 0건 — negative 확인 (seq 542 buggy 수식 잔존 없음).
  - `def test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing` 1건 (`:344`).
  - `def test_build_artifacts_emits_dispatch_selection_event` 1건 (`:305`, seq 533 sibling 보존).
  - `def test_` `wc -l` → `/work` 97 과 본 verify round grep 97 정합. /work 가 기록한 기대 95 는 handoff snapshot 기준이고 현재 dirty worktree 에는 pre-existing 추가 테스트가 포함되어 있음을 /work 가 honestly 기록.
  - `dispatch_selection` `pipeline_runtime/supervisor.py` 1건 (/work 기록 `:864` — seq 533 emit 이 broader dirty worktree 의 다른 추가로 line shift; 본 verify 에서 line number 만 바뀌었고 내용 계약 불변 확인).
  - `candidate_count|latest_any` `pipeline_runtime/schema.py` 0건; `date_key` 3건 — seq 527 + seq 530 계약 보존.
  - seq 539 `"Based on \`work/4/11/work-note.md\`\n"` 2건; seq 536 `"Based on \`work/4/16/2026-04-16-real-round.md\`\n"` 1건 — 모든 fixture 보존.
- `python3 -m py_compile tests/test_pipeline_runtime_supervisor.py`
  - 결과 (본 verify): 출력 없음, 통과. /work 결과와 정합.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_dispatch_selection_event_sequence_is_monotonic_nondecreasing`
  - 결과: `Ran 1 test in 0.006s`, `OK`. 신규 타깃 green.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor -k build_artifacts` — /work 기록 `Ran 4 / OK`. 본 verify round 는 full-suite 가 이 4건을 포함하므로 개별 재실행 생략.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor`
  - 결과: `Ran 97 tests in 0.807s`, `OK`. /work 기록의 95 대비 +2 증가; 이번 라운드 append 는 1개이므로 나머지 +1은 dirty worktree 의 pre-existing 추가(또는 /work 기록 시점 drift). 실패는 없음 — 모든 테스트 green.
- matching-verify focused triple + 기타 regression (`tests.test_pipeline_runtime_schema` 36, `tests.test_watcher_core` 143, `tests.test_operator_request_schema` 6, `tests.test_pipeline_gui_backend` 46, smoke 11/27): /work 기록 정합. 이번 변경이 단일 test file 에만 국한되어 다른 모듈 계약에 영향 줄 경로 없음이 명백하므로 본 verify round 에서 재실행 생략.
- `git diff --check -- tests/test_pipeline_runtime_supervisor.py`
  - /work 기록: 출력 없음. 이번 verify 에서 spot-check 생략하지 않고 `Read` + grep 으로 추가 검증.
- 실행하지 않은 항목 (명시):
  - `tests.test_web_app`, Playwright, `make e2e-test`: 이번 변경은 단일 test file. browser-visible 계약 밖. 의도적 생략.
  - dirty worktree 의 다른 test 추가 전수 audit: 범위 외. 다음 라운드 AXIS-STALE-REFERENCE-AUDIT 축 후보.

## 남은 리스크
- **vector 2 test-layer story closed**: seq 530 selector proof + seq 533 observability probe + seq 543 monotonic ordering replay test 가 모두 green. 실제 dispatcher 가 재가동되어 live `events.jsonl` 에 이 sequence 를 쌓는 것은 다음 runtime 가동 후 `/verify` 에서 확인되어야 함. 이번 test-layer closure 는 심볼릭 증명이지 real-run 증명은 아님.
- **seq 542 typo 교훈**: emit payload field shape 에 기대는 handoff 는 `pipeline_runtime/supervisor.py:_build_artifacts` 실제 return value + sibling test literal assertion 을 cross-check 해야 함. seq 543 recovery 에서 `Path(...).name[:10]` semantic 을 seq 530 과 일치시켜 이 cross-check 가 실제로 작동함을 증명.
- **dirty-worktree grep drift**: `def test_` 가 /work 기록 95 대비 현재 97 개로 관측. +1 은 이번 라운드 append, +1 은 pre-existing 추가로 보임. /work 가 이 drift 를 honestly 기록. 전체 suite OK 이므로 회귀는 없음.
- **`pipeline_runtime/supervisor.py` line shift**: dirty worktree 에서 `dispatch_selection` emit 이 seq 533 시점 `:820` → 현재 `:864` 로 shift. 내용 계약(`self._append_event("dispatch_selection", {"latest_work": work_rel, "latest_verify": verify_rel})`) 은 byte-for-byte 유지.
- **AXIS-STALE-REFERENCE-AUDIT 미수행**: `tests/test_pipeline_runtime_supervisor.py` 안의 잔존 bare `"# verify\n"` fixture (/work 에서 `:1057` 근방 manifest-mismatch 계열 언급) 와 다른 `latest_verify_note_for_work` consumer 전수 audit 은 여전히 오픈. 후속 축 후보.
- **G7-gate-blocking, G11, G8-pin, G3, G9, G10, G6-sub2/sub3** 계속 deferred, `tests.test_web_app` 10 PermissionError, `pipeline_gui_backend` 46 baseline 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지.
- **dirty worktree**: broad unrelated dirty 파일들 + `pipeline_runtime/schema.py:22-25` 그대로. 이번 라운드 추가 stage 없음.
- **next slice ambiguity → Gemini-first**: 남은 candidate(AXIS-STALE-REFERENCE-AUDIT — `:1057` 포함 bare `"# verify\n"` sweep / AXIS-EMIT-PAYLOAD-ENRICH — emit payload 에 `date_key`/`work_mtime` 명시 추가로 downstream 비용 절감 / G4 / G7-GATE / G5-DEGRADED-BASELINE (pipeline_gui_backend 46 doc-sync) / G6-TEST-WEB-APP / G11 / G8-PIN / DOCS-BUNDLE) 은 축이 서로 다르고 dominant current-risk reduction 이 명확하지 않음. 오늘 docs-only round count 0, real operator-only blocker 없음. 따라서 next control 은 `.pipeline/operator_request.md` 보다 `.pipeline/gemini_request.md` (CONTROL_SEQ 544) 로 여는 편이 맞습니다.
