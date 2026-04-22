# 2026-04-22 pipeline legacy name cleanup

## 변경 파일
- `watcher_core.py`
- `tests/test_watcher_core.py`
- `work/4/22/2026-04-22-pipeline-legacy-name-cleanup.md`
- `.pipeline/archive/2026-04-22/claude_handoff.20260422-013322.md` (gitignored generated archive)
- `.pipeline/archive/2026-04-22/gemini_request.20260422-010719.md` (gitignored generated archive)
- `.pipeline/archive/2026-04-22/gemini_advice.20260422-010227.md` (gitignored generated archive)
- `.pipeline/archive-stale-control-slots.sh`
- `watcher_prompt_assembly.py`
- `tests/test_pipeline_slot_archive.py`
- `.pipeline/README.md`

## 사용 skill
- `security-gate`: runtime control slot archive와 설정 fallback 경계를 건드려 local-first / audit / rollback 경계를 확인했습니다.
- `work-log-closeout`: 실제 변경, 실행한 명령, 남은 리스크를 `/work` 형식으로 남겼습니다.

## 변경 이유
- CONTROL_SEQ 739의 `pipeline_runtime_legacy_name_cleanup` handoff에 따라 blocked triage prompt 설정 키를 role-based canonical 이름으로 고정해야 했습니다.
- 기존 `codex_blocked_triage_prompt`는 운영 설정 호환을 위해 읽기 전용 fallback으로만 남기고, 새 설정은 `verify_blocked_triage_prompt`가 우선하도록 정리했습니다.
- `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`는 canonical slot이 이미 존재하는 stale legacy alias 파일이라 archive로 이동했습니다.

## 핵심 변경
- `watcher_core.py`의 blocked triage prompt 우선순위를 `verify_blocked_triage_prompt` → `verify_triage_prompt` → `codex_blocked_triage_prompt` → default로 변경했습니다.
- `tests/test_watcher_core.py`에 canonical prompt key가 legacy key보다 우선하는 테스트와 `codex_blocked_triage_prompt` fallback 유지 테스트를 추가했습니다.
- `_last_implement_handoff_sig`, `_last_advisory_request_sig`, `_last_advisory_advice_sig`는 이미 role-based 이름으로 정리되어 있음을 확인했고, path property 이름(`claude_handoff_path` 등)은 이번 slice에서 변경하지 않았습니다.
- `.pipeline/archive-stale-control-slots.sh --all-stale`를 `bash`로 실행했을 때 mtime 기준 때문에 canonical control 파일까지 archive되는 것을 확인했습니다. 즉시 `implement_handoff.md`, `advisory_request.md`, `advisory_advice.md`를 archive에서 원위치로 복구했고, legacy alias 세 파일만 archive 상태로 남겼습니다.
- 서브에이전트 재검토에서 같은 archive helper 리스크가 High로 확인되어, helper가 `pipeline_runtime.schema.parse_control_slots(...)` 기준 active control file을 보존하도록 수정했습니다. valid active control이 없을 때만 newest mtime fallback을 사용합니다.
- archive helper가 실제 archive 시 `.pipeline/archive/YYYY-MM-DD/archive-manifest.jsonl`에 repo-relative source/target, sha256, archived slot header, pre/post active control을 JSONL로 append하도록 보강했습니다.
- `watcher_prompt_assembly.py`의 blocked triage prompt body도 실제 active handoff path를 기준으로 만들게 해, legacy alias active 상태에서 `prompt_path`와 prompt 본문 `HANDOFF`가 갈라지지 않도록 했습니다.
- 최종 `parse_control_slots(.pipeline)` 확인 결과 active control은 `implement_handoff.md` CONTROL_SEQ 739입니다.

## 검증
- `bash -n .pipeline/archive-stale-control-slots.sh`
  - 결과: 통과
- `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py`
  - 결과: 통과
- `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_verify_blocked_triage_prompt_takes_precedence_over_legacy_keys tests.test_watcher_core.WatcherPromptAssemblyTest.test_codex_blocked_triage_prompt_remains_read_only_fallback`
  - 결과: `Ran 2 tests`, `OK`
- `bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - 결과: legacy alias 세 파일과 canonical 세 파일이 함께 archive됨. canonical 세 파일은 즉시 원위치 복구.
- `python3 -c "from pathlib import Path; from pipeline_runtime.schema import parse_control_slots; r = parse_control_slots(Path('.pipeline')); print('active:', r['active']['file'], r['active']['control_seq'])"`
  - 결과: `active: implement_handoff.md 739`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 191 tests`, `OK`
- `git diff --check`
  - 결과: 통과
- 서브에이전트 리뷰
  - 결과: archive helper active-control 보호 누락 High, blocked-triage legacy alias prompt path mismatch Medium 확인 후 수정.
- `python3 -m unittest tests.test_pipeline_slot_archive`
  - 결과: `Ran 5 tests`, `OK`; archive manifest JSONL 생성, repo-relative path, sha256, archived slot header, dry-run 무변경, append 기록 확인 포함.
- `PIPELINE_ARCHIVE_DRY_RUN=1 bash .pipeline/archive-stale-control-slots.sh --all-stale`
  - 결과: `SKIP protected control file implement_handoff.md`; stale canonical/advisory/operator 파일은 archive 대상 preview.
- 추가 focused watcher tests:
  - `python3 -m unittest tests.test_watcher_core.WatcherPromptAssemblyTest.test_verify_blocked_triage_prompt_takes_precedence_over_legacy_keys tests.test_watcher_core.WatcherPromptAssemblyTest.test_codex_blocked_triage_prompt_remains_read_only_fallback tests.test_watcher_core.WatcherPromptAssemblyTest.test_blocked_triage_prompt_uses_active_legacy_handoff_path`
  - 결과: 통과
- 최종 재확인:
  - `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 191 tests`, `OK`
  - `git diff --check`
  - 결과: 통과

## 남은 리스크
- `.pipeline/archive-stale-control-slots.sh --all-stale`는 이제 active `CONTROL_SEQ`/status 기준 control file은 보존하지만, stale canonical control files(`advisory_request.md`, `advisory_advice.md`, `operator_request.md`)는 여전히 archive 대상입니다. 운영자가 stale canonical slots도 root에 남겨야 하는 정책을 원하면 별도 옵션 분리가 필요합니다.
- legacy alias 파일은 root `.pipeline/`에서는 사라졌지만 archive에는 보존되어 있습니다. 오래된 run snapshot과 historical fixture 안의 legacy 이름은 이번 slice 범위 밖입니다.
- `codex_blocked_triage_prompt`와 일부 `codex_*`/`claude_*` 문자열은 compatibility alias, adapter plane, historical fixture 용도로 남아 있습니다.
- archive helper manifest는 archive 시 JSONL로 남기지만 runtime event stream과는 아직 연결하지 않았습니다. watcher/supervisor events까지 연결하는 것은 감사/정리성 후속 개선 후보이며 현재 High 리스크는 아닙니다.
- `pipeline_gui/backend.py`와 runtime schema의 control-slot read path에는 일부 중복이 남아 있습니다. 서브에이전트 검토 결과 Windows/WSL I/O adapter 계약 때문에 이번 라운드에서 단순 통합하지 않고 후속 cleanup 후보로 남기는 편이 안전합니다.
- `.pipeline/gui-runtime/_data`는 gitignored packaged runtime copy이므로 이번 tracked 변경에는 포함하지 않았습니다.
- 커밋/푸시/PR 작업은 수행하지 않았습니다. 기존 untracked protocol/source/work/verify/report 파일은 커밋 전 포함 범위를 다시 확인해야 합니다.
