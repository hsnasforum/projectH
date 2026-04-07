# 2026-04-05 Token Work Roundup

## 목적

2026-04-05 기준으로 진행한 token 관련 작업을 `report/token/` 아래에서 한 번에 이어 볼 수 있도록 정리합니다.

이 폴더는 token monitor / token collector / token DB / token query / token UI 같은 token 주제 작업 기록을 남기는 기준 폴더로 사용합니다.

## 오늘까지 반영된 범위

### 1. launcher quota 보강 초안

- `pipeline_gui/tokens.py`
  - Claude / Codex / Gemini 로컬 usage 로그를 읽어 launcher `Quota:` 라인에 표시하는 1차 경로를 추가했습니다.
- 현재 방향은 project별 attribution보다 전체 로컬 usage visibility를 먼저 확보하는 쪽입니다.
- 관련 초안 문서는 `report/token/2026-04-05-pipeline-token-monitoring-draft.md`에 정리했습니다.

### 2. WSL-side token collector 1차 뼈대

- `_data/token_schema.sql`
  - `raw_usage`, `collector_status`, `file_state`, `pipeline_event`, `job_usage_link` 테이블을 정의했습니다.
- `_data/token_parsers/`
  - `claude.py`, `codex.py`, `gemini.py`로 CLI별 파서를 분리했습니다.
- `_data/token_store.py`
  - SQLite 초기화, batch insert, collector status 갱신, file state 저장을 담당합니다.
- `_data/token_collector.py`
  - WSL 쪽에서 usage 로그와 `.pipeline/logs/*.jsonl`를 읽어 DB에 적재합니다.
- `_data/job_linker.py`
  - `slot_verify` dispatch window 기준으로 Codex usage를 job에 연결하는 1차 링크 계층을 둡니다.

### 3. pipeline lifecycle 연동

- `start-pipeline.sh`
  - `.pipeline/usage/` 생성
  - `collector.log` truncate
  - `usage.db` 유지
  - token collector tmux window 실행
  - `collector.pid` 저장
- `stop-pipeline.sh`
  - token collector 종료

### 4. 조회 계층 / 최소 GUI / 운영 안정성 보강

- `pipeline_gui/token_queries.py`
  - `collector_status`, 오늘 합계, agent별 합계, top jobs 조회를 typed object로 분리했습니다.
- `pipeline_gui/app.py`, `pipeline_gui/view.py`
  - launcher에서 DB 조회 결과를 읽어 최소 token overview panel을 표시합니다.
- `_data/job_linker.py`
  - 겹치는 `slot_verify` dispatch window에서 usage 1건이 여러 job에 중복 링크되지 않도록 전역 기준 best-match로 재링크합니다.
- `pipeline_gui/token_queries.py`
  - heartbeat 기준 `stale` collector 상태를 판정해 GUI에서 죽은 수집기를 running처럼 보이지 않게 했습니다.
- `tests/test_token_queries.py`, `tests/test_token_collector.py`
  - stale collector status, overlapping dispatch window 이중 링크 방지, stale scanning 상태 복구 테스트를 추가했습니다.

### 5. 첫 스캔 실측과 기본값 조정

- 새 DB 기준으로 `--once` 벤치를 4개 케이스에서 측정했습니다.
- 측정 결과
  - `since-days 7`
    - elapsed `7.664s`
    - scanned_files `278`
    - parsed_files `278`
    - usage_inserted `25052`
    - duplicates `11112`
    - retry_later `0`
    - db_size_mb `18.176`
  - `since-days 14`
    - elapsed `27.231s`
    - scanned_files `345`
    - parsed_files `345`
    - usage_inserted `130500`
    - duplicates `11112`
    - retry_later `0`
    - db_size_mb `108.645`
  - `since-days 30`
    - elapsed `55.534s`
    - scanned_files `882`
    - parsed_files `882`
    - usage_inserted `294694`
    - duplicates `11112`
    - retry_later `0`
    - db_size_mb `244.086`
  - 전체 스캔
    - elapsed `60.597s`
    - scanned_files `923`
    - parsed_files `923`
    - usage_inserted `351831`
    - duplicates `11112`
    - retry_later `0`
    - db_size_mb `292.055`
- 현재 로컬 환경에서는 `14일`이 첫 스캔 `27초대`로 부팅 기본값으로는 무겁다고 판단해 `start-pipeline.sh` 기본 collector 옵션을 `--since-days 7`로 낮췄습니다.
- 긴 히스토리는 이후 수동 재색인 또는 별도 백필 액션으로 분리하는 쪽이 안전합니다.

### 6. 수동 운영 UX 분리

- launcher `TOKENS` 패널에 수동 action을 두 개만 노출합니다.
  - `FULL HISTORY`
    - 기존 `usage.db` 유지
    - dedup 기반 누적 보강
  - `REBUILD DB`
    - 임시 DB 전체 스캔
    - 성공 시 기존 DB는 `usage.backup-<timestamp>.db`로 남기고 swap
- `30일 보강` 버튼은 현재 실측에서 `30일`과 `전체` 차이가 작아 초기 UI에서 제외했습니다.
- 수동 action은 실행 중 collector가 살아 있으면 잠시 멈췄다가 작업 후 다시 시작합니다.
- 진행 상태는 token panel `Action:` 줄에서 `phase / elapsed / scanned / parsed / insert / dup / retry`로 표시합니다.

### 7. collector spawn 경로 통일

- `start-pipeline.sh`와 GUI backend 모두 collector 복귀 경로를 `tmux usage-collector` window 우선으로 통일했습니다.
- tmux session이 없을 때만 background fallback을 허용합니다.
- `.pipeline/usage/` 아래에 다음 sidecar를 남깁니다.
  - `collector.pid`
  - `collector.pane_id`
  - `collector.window_name`
  - `collector.launch_mode`
- launcher `TOKENS` 상태줄은 현재 collector `launch_mode`와 tmux window 이름을 함께 표시합니다.
- 수동 action 뒤에는 기존 collector 실행 여부와 무관하게 collector를 다시 세웁니다.

### 8. fallback smoke 확인

- 임시 HOME + 임시 project로 실제 smoke를 수행했습니다.
- 확인 케이스
  - `tmux` 명령은 존재하지만 session은 없는 상태
  - session 없음 + `FULL HISTORY`
  - session 없음 + `REBUILD DB`
  - background fallback 이후 tmux session 생성 + collector 재시작
- 결과
  - session 없음 + `FULL HISTORY`
    - action 성공
    - collector 재기동 성공
    - `launch_mode=background`
    - `pane_id/window_name` 비어 있음
    - heartbeat 갱신 확인
  - session 없음 + `REBUILD DB`
    - action 성공
    - swap 이후 collector 재기동 성공
    - `launch_mode=background`
    - backup DB 생성 확인
  - tmux session 복구 후 재시작
    - `launch_mode=tmux`
    - `window_name=usage-collector`
    - `pane_id` 기록 확인

## 현재 설계 판단

### 이미 잠근 것

- GUI 직접 파싱 대신 WSL 수집기 + SQLite 적재 구조
- CLI별 파서 분리
- `actual_cost_usd` / `estimated_cost_usd` 분리
- `job_usage_link.confidence`, `job_usage_link.link_method`
- `collector_status` 기반 상태 가시화
- `--since-days` 지원
- JSONL trailing partial line / Gemini partial JSON retry-later 처리
- `Codex slot_verify dispatch` + `Claude artifact_seen work window` + `Gemini notify recent job window` 3단 attribution 초안

### 아직 남은 것

- 수동 action을 watcher log 또는 별도 token log와 더 촘촘히 연결할지 결정
- Claude/Gemini attribution confidence를 실제 운영 로그 기준으로 더 다듬을지 결정
- 모델별 drill-down / 7일 추이 같은 2단계 UI는 아직 미구현

### 최근 보강: Claude/Gemini attribution 1차

- `_data/job_linker.py`
  - 기존 `slot_verify` Codex 링크만 재계산하던 구조를 `pipeline_event` 전체 job 집합 기준으로 재계산하도록 넓혔습니다.
  - `artifact_seen`가 `work/` 경로를 가리키는 경우 Claude 작업 완료 anchor로 보고, 이전 artifact와 현재 artifact 사이 usage를 현재 job에 연결합니다.
  - `gemini_notify`가 존재하는 경우에는 notify 직전 가장 최근의 real job event를 찾아 Gemini usage를 낮은 confidence로 연결합니다.
  - 각 링크는 계속 `link_method`, `confidence`, `note`를 남겨서 “왜 붙었는지”가 설명 가능하도록 유지했습니다.
- `tests/test_token_collector.py`
  - Claude usage가 `artifact_seen_work_window`로 연결되는지
  - Gemini usage가 `gemini_notify_recent_job_window`로 연결되는지
  를 회귀 테스트로 추가했습니다.

### 최근 보강: confidence calibration 보조 조회

- `pipeline_gui/token_queries.py`
  - `get_link_method_summaries()`
  - `get_link_samples()`
  - `get_unlinked_usage_counts()`
  를 추가해 link method별 이벤트 수, 평균 confidence, 저신뢰 이벤트 수, 샘플 row, unlinked usage 수를 read-only로 조회할 수 있게 했습니다.
- `_data/token_link_audit.py`
  - WSL에서 `usage.db`를 바로 읽어 confidence calibration용 summary / sample / unlinked 현황을 CLI로 출력하는 helper를 추가했습니다.
- `tests/test_token_queries.py`
  - summary / sample / unlinked 조회가 기대값대로 나오는지 회귀 테스트를 추가했습니다.

### 최근 보강: Claude confidence 보수화

- 실제 `.pipeline/usage/usage.db`를 생성한 뒤 calibration helper로 샘플을 확인해 보니, Claude `artifact_seen_work_window`가 `fallback_before_45m`일 때 30분 이상 떨어진 usage까지 붙는 오탐이 확인됐습니다.
- `_data/job_linker.py`
  - Claude fallback window를 `45분`에서 `10분`으로 축소했습니다.
  - `-5분 ~ +30초`는 `0.70`
  - `-10분 ~ +30초`는 `0.55`
  - 그보다 오래된 Claude usage는 링크하지 않고 unlinked로 남기도록 바꿨습니다.
- `tests/test_token_collector.py`
  - `10분 초과 오래된 Claude usage는 link하지 않는다`는 회귀 테스트를 추가했습니다.
- 실제 재링크 후 관측
  - Claude linked events: `1490 -> 1276`
  - Claude avg confidence: `0.62 -> 0.68`
  - Claude unlinked events: `9236 -> 9450`
  - 즉, 더 적게 붙이되 더 강한 링크만 남기는 방향으로 이동했습니다.
- Gemini는 현재 운영 DB에 usage/link 사례가 아직 없어서 이번 round에서는 calibration 결정을 내리지 않았습니다.

### 최근 보강: launcher job 표 신뢰도 노출

- `pipeline_gui/token_queries.py`
  - `get_top_jobs_today()`가 job별 대표 `primary_link_method`와 `low_confidence_events`를 함께 반환하도록 보강했습니다.
- `pipeline_gui/app.py`
  - launcher `Top jobs` 줄에 비용 외에도
    - 대표 method (`dispatch` / `artifact` / `gemini`)
    - 대표 confidence (`c=...`)
    - 저신뢰 비율 (`low=a/b`)
  를 같이 표시하도록 바꿨습니다.
- `pipeline_gui/token_queries.py`, `pipeline_gui/app.py`
  - `Agents` 줄은 source별 `linked_events`를 같이 보고, usage는 있지만 linked sample이 없는 경우 `no-link`를 표시하도록 보강했습니다.
- 목적
  - 운영 화면에서 바로 “이 job 비용이 강한 링크 위주인지, 휴리스틱 비중이 큰지”를 해석할 수 있게 하기 위함입니다.

### 최근 보강: token action 진행률 표시

- `_data/token_collector.py`
  - progress payload와 최종 summary에 `total_files`, `progress_percent`를 추가했습니다.
  - 수동 `FULL HISTORY` / `REBUILD DB` 실행 시 전체 대상 파일 수 기준으로 `0~100%` 진행률을 계산합니다.
- `pipeline_gui/app.py`
  - `Action:` 줄에 `XX% · scan x/y`를 함께 표시하도록 바꿨습니다.
- `tests/test_token_collector.py`
  - progress callback이 `0% -> 100%`와 `total_files`를 함께 내보내는지 회귀 테스트를 추가했습니다.

### 최근 보강: progress 전달과 loading placeholder 정리

- `pipeline_gui/backend.py`
  - 수동 `FULL HISTORY` / `REBUILD DB` 실행 시 child collector를 `python3 -u`로 실행하고 `bufsize=1` line-buffering을 명시해, progress JSON이 launcher로 더 빨리 전달되도록 보강했습니다.
  - background/tmux collector spawn도 같은 `python3 -u` 경로로 통일했습니다.
- `_data/token_collector.py`
  - `--once --progress` 최종 summary 출력도 `flush=True`로 맞췄습니다.
- `pipeline_gui/app.py`
  - token action 시작 직후부터 `Action: ... 0% ...` 형태가 바로 보이도록 초기 progress payload를 공통 formatter로 그리게 바꿨습니다.
  - 아직 `usage.db`가 없는 project에서 수동 action이 돌고 있는 동안은 `Collector/Today/Agents/Top jobs`를 `missing`/`0`/`-` 대신 `loading...`으로 표시하도록 정리했습니다.
- 테스트
  - `tests/test_token_backend.py`: `run_token_collector_once()`가 `python3 -u`와 progress forwarding을 유지하는지 확인하는 회귀 테스트를 추가했습니다.
  - `tests/test_pipeline_gui_app.py`: DB가 없는 상태의 token action 동안 `loading...` placeholder가 유지되는지 확인하는 회귀 테스트를 추가했습니다.

### 최근 보강: latest-day fallback과 비동기 quota refresh

- `pipeline_gui/token_queries.py`
  - `TOKENS` 패널 기본 기준일이 오늘인데 usage가 비어 있으면, `raw_usage`의 최신 `day`로 자동 fallback하도록 `display_day`를 추가했습니다.
  - 이로 인해 “오늘은 비어 있는데 최근 usage가 있는 project”에서도 `Agents`/`Today`가 `—`로 비지 않고 최근 집계를 바로 볼 수 있습니다.
- `pipeline_gui/app.py`
  - agent 카드의 `Quota:` summary는 전역 CLI usage 로그 스캔이 끝날 때까지 전체 snapshot을 기다리지 않도록 비동기 캐시 refresh로 분리했습니다.
  - 수동 `FULL HISTORY` / `REBUILD DB` 완료 직후에는 다음 poll을 기다리지 않고 token dashboard와 usage summary를 즉시 다시 읽도록 보강했습니다.
  - `Top jobs`가 비어 있지만 token usage/agent totals는 존재하는 경우, `Top jobs: no linked jobs yet`로 표시해 “표시 실패”와 “아직 링크 없음”을 구분합니다.
- 테스트
  - `tests/test_token_queries.py`: 오늘 usage가 없을 때 최신 usage day로 fallback되는지 확인하는 회귀 테스트를 추가했습니다.

### 최근 보강: FULL HISTORY 실제 full rescan + pre-step progress

- `_data/token_collector.py`
  - `force_rescan`/`--force-rescan`을 추가해, 기존 `file_state`가 있어도 전체 로그를 다시 스캔할 수 있게 했습니다.
  - 이 경로에서는 dedup만 믿고 다시 읽으므로, `FULL HISTORY`가 이름대로 “전체 히스토리 보강”이 됩니다.
- `pipeline_gui/backend.py`

### 최근 보강: token reader 중복 정리 2차

- `pipeline_gui/token_usage_shared.py`
  - Claude / Codex / Gemini usage reader를 로컬 launcher 경로와 WSL launcher 경로가 함께 쓰는 공유 모듈로 분리했습니다.
  - 공통 summary 생성, JSONL decode, timestamp 파싱, usage 집계 로직을 이 모듈 한 곳에 모았습니다.
- `pipeline_gui/tokens.py`
  - 더 이상 큰 `_WSL_TOKEN_SCRIPT` 문자열을 들고 있지 않고, WSL에서도 `token_usage_shared.py`를 직접 실행해 같은 구현을 사용합니다.
  - local wrapper도 project 인자를 무시하는 공통 helper를 거쳐 shared reader로 위임하도록 정리했습니다.
- `tests/test_pipeline_gui_tokens.py`
  - WSL 경로가 실제로 `token_usage_shared.py`를 실행하는지 회귀 테스트를 추가했습니다.

### 최근 보강: token action UI 핸들러 중복 정리

- `pipeline_gui/app.py`
  - `FULL HISTORY` / `REBUILD DB` 버튼의 공통 시작 흐름을 `_start_token_maintenance_action()`으로 묶었습니다.
  - 실제 실행 후 `done/error`, dashboard refresh, usage refresh, unlock 처리도 `_run_token_maintenance_action()`으로 공통화했습니다.
  - action별로 다른 점은 dialog 문구, backend 실행 함수, 완료 문구 builder만 남기고 나머지 UI 흐름 중복을 줄였습니다.
- `tests/test_pipeline_gui_app.py`
  - 공통 시작 helper가 lock/progress/thread 시작을 한 번에 처리하는지
  - 공통 실행 helper가 done text, refresh, unlock을 한 번에 enqueue하는지
  회귀 테스트를 추가했습니다.

### 최근 보강: token maintenance backend 결과/에러 중복 정리

- `pipeline_gui/backend.py`
  - `backfill_token_history()`와 `rebuild_token_db()`가 공통 결과 dict shape를 쓰도록 `_token_maintenance_result()` helper를 추가했습니다.
  - `action_error` / `restart_error` 병합 규칙도 `_raise_token_maintenance_errors()`로 묶어, backend 쪽 token maintenance 에러 처리 중복을 줄였습니다.
  - 이로 인해 backfill/rebuild 모두 `action`, `summary`, `backup_path`, `collector_was_running` 형태를 같은 기준으로 반환합니다.
- `tests/test_token_backend.py`
  - backfill 결과에도 공통 `backup_path` shape가 유지되는지
  - 공통 에러 helper가 action/restart 실패를 합쳐 올리는지
  회귀 테스트를 추가했습니다.

### 최근 보강: token dashboard query 공유 모듈 분리

- `pipeline_gui/token_dashboard_shared.py`
  - launcher token dashboard가 읽는 SQL과 payload 조립 로직을 로컬/WSL이 함께 쓰는 공유 모듈로 분리했습니다.
  - `collector_status`, `today_totals`, `agent_totals`, `top_jobs`, latest-day fallback을 이 모듈 한 곳에서 조립합니다.
- `pipeline_gui/token_queries.py`
  - 더 이상 큰 `_WSL_TOKEN_QUERY_SCRIPT` 문자열을 들고 있지 않고, WSL에서도 `token_dashboard_shared.py`를 직접 실행합니다.
  - 로컬 `load_token_dashboard()`도 같은 shared payload를 normalize하는 경로로 맞춰 dashboard query drift를 줄였습니다.
- `tests/test_token_queries.py`
  - Windows/WSL 경로가 실제로 `token_dashboard_shared.py`를 호출하는지 회귀 테스트를 추가했습니다.

### 최근 보강: token query filter / row mapping 중복 정리

- `pipeline_gui/token_queries.py`
  - audit 조회 3개에서 반복되던 `WHERE` 절 조립을 `_build_usage_filters()`로 묶었습니다.
  - `sqlite3.Row -> dataclass` 변환도 `_row_as_dataclass()` / `_rows_as_dataclasses()`로 공통화했습니다.
  - empty dashboard 반환도 `_empty_dashboard()`로 정리해 query helper 내부 반복을 줄였습니다.
- 목적
  - `get_link_method_summaries()`, `get_link_samples()`, `get_unlinked_usage_counts()`의 drift 포인트를 줄이고, token query 파일을 더 읽기 쉽게 유지하기 위함입니다.

### 최근 보강: token panel 문자열 formatter 중복 정리

- `pipeline_gui/app.py`
  - token panel의 `Collector`, `Today/Latest`, `Agents`, `Top jobs` 표시 문자열을 각각 formatter helper로 분리했습니다.
  - `loading/missing/no-link` 판단, job link method 축약, agent/job segment 조립이 한 곳 기준을 쓰도록 정리했습니다.
  - 기존 `_apply_token_dashboard()`는 값 읽기와 helper 호출 위주로 얇아졌습니다.
- `tests/test_pipeline_gui_app.py`
  - job segment formatter가 `dispatch_slot_verify_window`를 `dispatch`로 축약하고, confidence / low count를 그대로 붙이는지 회귀 테스트를 추가했습니다.

### 최근 보강: launcher 공통 formatter / button state 중복 정리

- `pipeline_gui/formatting.py`
  - compact count 표기를 공용 `format_compact_count()` helper로 분리했습니다.
- `pipeline_gui/tokens.py`, `pipeline_gui/app.py`
  - 각각 따로 들고 있던 `1.2k / 1.0M` count formatter 중복을 공용 helper 사용으로 정리했습니다.
- `pipeline_gui/app.py`
  - project error 상태와 일반 snapshot apply 경로에서 반복되던 main control button state 토글을 `_set_main_button_states()`로 묶었습니다.
- `tests/test_pipeline_gui_app.py`
  - `_set_main_button_states()`가 `disabled`/`ready` 두 모드를 올바르게 적용하는지 회귀 테스트를 추가했습니다.
  - `FULL HISTORY`와 `REBUILD DB`는 수동 one-shot 실행 시 `force_rescan=True`로 collector를 호출하도록 바꿨습니다.
  - 기존 collector를 잠시 멈춰야 할 때는 `stopping_collector`, 완료 후 재기동할 때는 `starting_collector` progress 이벤트를 먼저/나중에 보내도록 정리했습니다.
- `pipeline_gui/app.py`
  - token action 진행 표시에 `stopping collector`, `starting collector` 단계가 읽히도록 phase 문자열을 공백형으로 정리했습니다.
- 테스트
  - `tests/test_token_collector.py`: unchanged 파일도 `force_rescan=True`면 다시 스캔하고 dedup로 0 insert가 되는지 확인하는 회귀 테스트를 추가했습니다.
  - `tests/test_token_backend.py`: backfill이 `force_rescan=True`로 실행되고 stopping/starting progress를 보내는지 확인하는 회귀 테스트를 추가했습니다.

### 최근 보강: 선택 agent 기준 token detail

- `pipeline_gui/view.py`, `pipeline_gui/app.py`
  - `TOKENS` 패널에 `Selected <AGENT>` 줄을 추가했습니다.
  - agent 카드를 클릭하면 현재 선택된 agent 기준으로
    - global usage summary
    - latest-day DB 합계
    - linked/no-link 상태
    를 함께 보여주도록 정리했습니다.
- 테스트
  - `tests/test_pipeline_gui_app.py`: loading placeholder와 selected agent detail formatting 회귀 테스트를 추가했습니다.

### 최근 보강: token reader 내부 중복 정리

- `pipeline_gui/tokens.py`
  - local usage reader에서 반복되던
    - JSONL line decode
    - ISO timestamp 안전 파싱
    - 파일 mtime 조회
    helper를 공통 함수로 정리했습니다.
  - 기능 변화 없이 token reader 내부 drift 포인트를 줄이는 목적의 정리입니다.
- 검증
  - `tests/test_pipeline_gui_tokens.py` 회귀를 다시 통과했습니다.

## 현재 파일 묶음

- 초안/설계
  - `report/token/2026-04-05-pipeline-token-monitoring-draft.md`
- 수집기 구현
  - `_data/token_schema.sql`
  - `_data/token_store.py`
  - `_data/token_collector.py`
  - `_data/job_linker.py`
  - `_data/token_parsers/base.py`
  - `_data/token_parsers/claude.py`
  - `_data/token_parsers/codex.py`
  - `_data/token_parsers/gemini.py`
- pipeline 연동
  - `start-pipeline.sh`
  - `stop-pipeline.sh`
- 테스트
  - `tests/test_pipeline_gui_tokens.py`
  - `tests/test_token_collector.py`

## 기록 원칙

- token 관련 설계 메모, collector 보강, query 설계, GUI token tab 설계/구현 기록은 `report/token/`에 누적합니다.
- 작업 로그를 별도 `work/`에 남길지 여부는 사용자 승인 기준을 따릅니다.
