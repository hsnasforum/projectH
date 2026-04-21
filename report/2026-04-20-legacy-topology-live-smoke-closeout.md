# 2026-04-20 legacy topology live smoke closeout

## 변경 파일
- `verify/4/20/2026-04-20-legacy-topology-live-smoke-closeout.md`

## 사용 skill
- `round-handoff`: 최신 `/work`와 `/verify`를 먼저 읽고, legacy topology live smoke를 직접 재실행한 뒤 `/verify` closeout만 남겼습니다.

## 변경 이유
- 남아 있던 topology 리스크는 “swapped profile은 live로 닫았지만 legacy topology는 아직 live smoke 재실행으로 닫지 못했다”는 1건뿐이었습니다.
- 이번 라운드는 새 구현 없이 `.pipeline/smoke-three-agent-arbitration.sh`의 `legacy` 모드를 실제로 실행해, legacy binding(`implement=Claude`, `verify=Codex`, `advisory=Gemini`)이 현재 runtime/topology truth-lock 이후에도 live에서 그대로 닫히는지 확인하는 verification-only closeout입니다.

## 핵심 변경
- 코드 변경은 없었습니다. live smoke evidence만 추가 확보했습니다.
- `PIPELINE_SMOKE_TOPOLOGY=legacy`로 실행한 smoke-local profile은 아래 binding으로 기록됐습니다.
  - `implement=Claude`
  - `verify=Codex`
  - `advisory=Gemini`
- live run 결과, advisory 단계에서 `gemini_advice.md`가 `STATUS: advice_ready`, `CONTROL_SEQ: 2`로 생성됐고, 이어 verify follow-up이 Codex lane으로 전달된 뒤 final control slot은 `claude_handoff.md` 하나만 `STATUS: implement`, `CONTROL_SEQ: 2`로 갱신됐습니다.
- smoke-local report는 `report/gemini/2026-04-03-live-arbitration-smoke.md` 1건이 생성됐고, `operator_request.md`는 열리지 않았습니다.
- `scripts/pipeline_runtime_gate.py check-operator-classification`도 same session(`ai-pipeline-smoke-legacy`) 기준으로 `structured operator classification_source OK`를 반환해 classification fallback이 재주입되지 않음을 확인했습니다.
- 이번 smoke 산출물 base dir은 `.pipeline/live-arb-smoke-oRjZkn`입니다.

## 검증
- `bash -n .pipeline/smoke-three-agent-arbitration.sh`
  - 결과: 통과
- `command -v claude && command -v codex && command -v gemini`
  - 결과: 세 CLI 모두 PATH에서 확인
- `PIPELINE_SMOKE_TOPOLOGY=legacy PIPELINE_SMOKE_SESSION=ai-pipeline-smoke-legacy PIPELINE_SMOKE_KEEP_SESSION_ON_FAILURE=1 PIPELINE_SMOKE_KEEP_SESSION_ON_SUCCESS=0 bash ./.pipeline/smoke-three-agent-arbitration.sh`
  - 결과: `3-agent arbitration smoke OK`
  - stdout evidence:
    - `topology: legacy`
    - `base_dir: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn`
    - `smoke_profile: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn/.pipeline/config/agent_profile.json`
    - `watcher_log: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn/watcher.log`
    - `gemini_advice: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn/gemini_advice.md`
    - `claude_handoff: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn/claude_handoff.md`
    - `operator_request: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn/operator_request.md`
    - `report_dir: /home/xpdlqj/code/projectH/.pipeline/live-arb-smoke-oRjZkn/report/gemini`
- `cat .pipeline/live-arb-smoke-oRjZkn/.pipeline/config/agent_profile.json`
  - 결과: `role_bindings`가 `Claude/Codex/Gemini` legacy topology로 기록됨
- `cat .pipeline/live-arb-smoke-oRjZkn/gemini_advice.md`
  - 결과: `STATUS: advice_ready`, `CONTROL_SEQ: 2`
- `cat .pipeline/live-arb-smoke-oRjZkn/claude_handoff.md`
  - 결과: `STATUS: implement`, `CONTROL_SEQ: 2`
- `test -f .pipeline/live-arb-smoke-oRjZkn/operator_request.md`
  - 결과: 파일 없음
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --session ai-pipeline-smoke-legacy check-operator-classification`
  - 결과: `structured operator classification_source OK`

## 남은 리스크
- 이번 라운드로 “legacy topology live rerun 미실시” 리스크는 해소됐습니다.
- 다만 topology matrix를 상시 gate에 묶는 wrapper/hardening은 아직 별도 과제로 남아 있습니다. 이번 closeout은 existing matrix-capable smoke를 legacy 모드로 한 번 더 live 검증한 수준이며, 추가 자동화 확장은 범위 밖이었습니다.
