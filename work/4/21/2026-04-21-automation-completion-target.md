# 2026-04-21 automation completion target

## 변경 파일
- `AGENTS.md`
- `CLAUDE.md`
- `GEMINI.md`
- `PROJECT_CUSTOM_INSTRUCTIONS.md`
- `.pipeline/README.md`
- `.pipeline/operator_request.md`
- `work/README.md`
- `verify/README.md`
- `docs/projectH_pipeline_runtime_docs/01_개발계획서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `verify/4/21/2026-04-21-no-soak-automation-handoff.md`
- `work/4/21/2026-04-21-automation-completion-target.md`

## 사용 skill
- `mvp-scope`: 자동화 완성 목표를 현재 shipped contract, 다음 단계 목표, 장기 north star로 분리했습니다.
- `work-log-closeout`: 실제 변경 파일과 실행한 검증만 기준으로 closeout을 남겼습니다.

## 변경 이유
- operator의 최신 방향은 pipeline automation이 일반적인 다음 작업 선택, 애매한 선택지, stall, rollover, recovery 문제에서 사용자를 호출하지 않는 쪽입니다.
- 문제 발생 시 implement / verify-handoff / advisory owner가 먼저 상의하고, 재귀 개선과 운영 학습으로 같은 문제가 다음에 더 작게 닫히도록 해야 합니다.

## 핵심 변경
- 자동화 완성 목표를 `사용자 호출 최소화`, `에이전트 회의/중재 우선`, `재귀 개선/운영 학습/진화적 후보 비교`로 명시했습니다.
- `재귀학습`은 현재 단계에서 모델 가중치 학습이 아니라 `/work`, `/verify`, incident family, replay test, shared helper, runtime surface로 남는 repo-local operational learning으로 정의했습니다.
- `진화적 탐색`은 current evidence와 milestone에 묶인 bounded candidate comparison으로 정의했고, broad random exploration이나 사용자에게 선택지를 되돌리는 방식은 제외했습니다.
- `.pipeline/operator_request.md` seq 696에도 같은 목표를 반영해 런타임 재시작 후 verify/handoff owner가 바로 읽을 수 있게 했습니다.
- 안전 경계는 유지했습니다. destructive write, auth/credential, approval-record, truth-sync, publication boundary는 여전히 explicit approval과 audit trail 대상입니다.

## 검증
- `git diff --check -- AGENTS.md CLAUDE.md GEMINI.md PROJECT_CUSTOM_INSTRUCTIONS.md .pipeline/README.md .pipeline/operator_request.md work/README.md verify/README.md docs/projectH_pipeline_runtime_docs/01_개발계획서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md verify/4/21/2026-04-21-no-soak-automation-handoff.md work/4/21/2026-04-21-automation-completion-target.md` → 통과

## 남은 리스크
- 이번 변경은 목표/운영 문서와 handoff 동기화입니다. 실제 자동 회의, replay 생성, 후보 비교 자동화의 세부 구현은 후속 watcher/supervisor/launcher 슬라이스에서 닫아야 합니다.
- 현재 런타임은 앞선 확인 기준 `STOPPED` 상태였으므로 live lane 직접 전달은 하지 못했고, rolling control slot과 persistent notes에 반영했습니다.
