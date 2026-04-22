# 2026-04-22 runtime legacy control cleanup closeout

## 변경 파일
- `work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`

## 사용 skill
- `security-gate`: watcher runtime/control slot 이동이 canonical control 파일을 잘못 보관하지 않는지 확인했습니다.
- `finalize-lite`: 실행한 검증, 미실행 항목, 문서 동기화 필요 여부, 남은 리스크를 구현 종료 기준으로 정리했습니다.
- `work-log-closeout`: 실제 확인/실행 결과만 기준으로 이 `/work` closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 739의 pipeline runtime legacy naming cleanup handoff를 implement lane에서 처리하고, 코드/아카이브/검증 상태를 사실대로 남기기 위해서입니다.
- handoff의 코드 변경 항목은 현재 작업트리에 이미 반영되어 있었고, 루트 legacy physical control 파일도 이미 없는 상태였으므로 새 runtime code diff는 만들지 않았습니다.

## 핵심 변경
- `watcher_core.py`의 blocked triage prompt read path가 `verify_blocked_triage_prompt`를 canonical key로 먼저 읽고 `codex_blocked_triage_prompt`를 fallback으로 유지하는 상태임을 확인했습니다.
- `watcher_core.py`와 `tests/test_watcher_core.py`의 internal state sig 변수는 `_last_implement_handoff_sig`, `_last_advisory_request_sig`, `_last_advisory_advice_sig` 이름으로 이미 정리되어 있음을 확인했습니다.
- 루트 `.pipeline/claude_handoff.md`, `.pipeline/gemini_request.md`, `.pipeline/gemini_advice.md`는 이미 없고, 오늘자 archive에는 `claude_handoff.20260422-013322.md`, `gemini_request.20260422-010719.md`, `gemini_advice.20260422-010227.md`가 존재함을 확인했습니다.
- `PIPELINE_ARCHIVE_DRY_RUN=1 bash .pipeline/archive-stale-control-slots.sh --all-stale`는 `advisory_request.md`, `advisory_advice.md`, `operator_request.md`까지 archive 대상으로 표시해 handoff 제약과 충돌하므로 실제 `--all-stale` 실행은 하지 않았습니다.
- 대신 legacy 파일 3개만 명시해 `bash .pipeline/archive-stale-control-slots.sh claude_handoff.md gemini_request.md gemini_advice.md`를 실행했고 모두 `SKIP missing`으로 끝나 canonical control 파일은 보존됐습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md` 통과: `ea614800cbcb9071d66d833bf12903d409683af81b4c5d823d6e2353521eeea8`
- `PIPELINE_ARCHIVE_DRY_RUN=1 .pipeline/archive-stale-control-slots.sh --all-stale` 실패: script executable bit가 없어 `Permission denied`
- `PIPELINE_ARCHIVE_DRY_RUN=1 bash .pipeline/archive-stale-control-slots.sh --all-stale` 통과: dry-run 결과 canonical advisory/operator slot도 archive 대상으로 표시됨을 확인
- `bash .pipeline/archive-stale-control-slots.sh claude_handoff.md gemini_request.md gemini_advice.md` 통과: legacy root slot 3개 모두 `SKIP missing`
- `python3 -m py_compile watcher_core.py` 통과
- `python3 -m unittest tests.test_watcher_core` 통과 (`191 tests`)
- `python3 -c "from pathlib import Path; from pipeline_runtime.schema import parse_control_slots; r = parse_control_slots(Path('.pipeline')); print('active:', r['active']['file'], r['active']['control_seq'])"` 통과: `active: implement_handoff.md 739`
- `git diff --check` 통과

## 남은 리스크
- handoff에는 `--all-stale` 실제 실행이 적혀 있었지만, dry-run상 canonical `advisory_request.md` / `advisory_advice.md` / `operator_request.md`를 보관할 수 있어 실제 실행하지 않았습니다. 이는 handoff의 "do not archive advisory_request/advisory_advice" 제약을 우선한 결정입니다.
- `.pipeline/archive-stale-control-slots.sh`는 현재 executable bit가 없어 직접 실행 형식으로는 실패합니다. 이번 slice에서는 스크립트 권한 변경이 handoff 범위가 아니어서 `bash`로만 실행했습니다.
- 이번 round는 runtime code를 새로 수정하지 않았습니다. verify/handoff owner는 CONTROL_SEQ 739 handoff의 코드 변경이 이미 반영된 선행 상태인지, 그리고 `--all-stale` 제약 충돌을 별도 follow-up으로 볼지 판단해야 합니다.
