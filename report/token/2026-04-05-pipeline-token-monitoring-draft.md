# 2026-04-05 Pipeline Token Monitoring Draft

## 목적

`toktrack`의 Rust TUI를 직접 붙이지 않고, 그 저장 로그 파싱 아이디어를 `pipeline_gui`에 맞는 Python 모듈로 재구현하는 초안입니다.

현재 목표는 다음 두 가지입니다.

1. launcher의 agent 카드 `Quota:` 라인을 pane 텍스트 추정치보다 실제 로컬 usage 로그에 더 가깝게 보강
2. 현재 document-first MVP 범위를 넘지 않는 read-only local token monitoring 기반 마련

현재 operator 의도는 `프로젝트별 attribution`보다 `로컬 전체 기준 token visibility`를 우선 확보하는 것입니다.

## 현재 shipped 범위

- `pipeline_gui/tokens.py`가 로컬 CLI usage 로그를 읽습니다.
- 1차 통합 지점은 launcher agent 카드의 `Quota:` 줄입니다.
- 기존 pane 텍스트 기반 quota 추정은 fallback으로 유지합니다.
- write/approval/runtime 동작은 바꾸지 않습니다.

## 참고한 외부 소스

- `toktrack` README
- `toktrack` Claude parser
- `toktrack` Codex parser
- `toktrack` Gemini parser

핵심은 "어디에 어떤 usage 로그가 저장되는지"와 "어떤 필드를 토큰 계산에 쓰는지"만 참고하고, 구현은 projectH용 Python 코드로 다시 작성하는 것입니다.

## 데이터 소스 초안

### Claude

- 경로: `~/.claude/projects/**/*.jsonl`
- 주로 읽는 필드:
  - `message.usage.input_tokens`
  - `message.usage.output_tokens`
  - `message.usage.cache_creation_input_tokens`
  - `message.usage.cache_read_input_tokens`
- 1차 표시 기준:
  - project 구분 없이 로컬 전체 usage 로그를 합산

### Codex

- 경로: `~/.codex/sessions/**/*.jsonl`
- 주로 읽는 필드:
  - `event_msg.payload.type == "token_count"`
  - `payload.info.total_token_usage.*`
  - `payload.info.last_token_usage.*`
  - `payload.rate_limits.primary.used_percent`
  - `payload.rate_limits.primary.resets_at`
- 1차 표시 기준:
  - project 구분 없이 로컬 전체 usage 로그를 합산

### Gemini

- 경로: `~/.gemini/tmp/*`
- 주로 읽는 후보 필드:
  - `usageMetadata.promptTokenCount`
  - `usageMetadata.candidatesTokenCount`
  - `usageMetadata.cachedContentTokenCount`
  - `usageMetadata.thoughtsTokenCount`
  - `usageMetadata.toolUsePromptTokenCount`
- 1차 표시 기준:
  - `.project_root` 유무와 무관하게 로컬 전체 usage 로그를 best-effort로 읽음
- 현재 로컬 샘플에는 `usageMetadata`가 보이지 않는 경우가 있어, 1차는 best-effort로 둡니다.

## launcher 연결 초안

### 현재 연결

- snapshot build: `pipeline_gui/app.py`
- agent 카드 UI: `pipeline_gui/view.py`
- pane 텍스트 기반 fallback quota: `pipeline_gui/agents.py`

### 1차 구현

- `pipeline_gui/tokens.py`
  - `collect_claude_usage()`
  - `collect_codex_usage()`
  - `collect_gemini_usage()`
  - `collect_token_usage()`
  - `format_token_usage_note()`
- snapshot에 `token_usage`를 추가
- `_apply_snapshot()`에서 usage summary가 있으면 `Quota:` 줄에 우선 반영

예시:

- `Quota: 14% used · Sess 42.0k · Reset 03:00`
- `Quota: Sess 18.2k · Today 44.3k`

여기서 `Sess` / `Today`는 UI 가독성을 위해 기본적으로 cache token을 제외한 사용량으로 표시하고,
`cached_tokens`는 내부 summary 필드로만 유지합니다.

## Windows exe 고려

launcher는 Windows exe여도 실제 runtime과 project는 WSL 쪽을 봅니다.

따라서 token monitor도 Windows 로컬 파일을 읽는 게 아니라, WSL 내부 홈 디렉터리의 CLI usage 로그를 읽어야 합니다.

1차 구현은:

- Linux/WSL 내부 실행: Python이 직접 로컬 파일 파싱
- Windows exe: WSL 안에서 `python3 -c` 스크립트를 실행해 usage summary를 JSON으로 받아옴

즉 현재 방향은 "Rust 바이너리 번들"이 아니라 "WSL 내부 로그 파싱 결과만 가져오는 Python adapter"입니다.

## 현재 한계

1. project별 attribution은 아직 아님
- 현재 1차 목표는 project 분리보다 전체 usage visibility입니다.
- 나중에 필요하면 별도 opt-in project filter를 추가할 수 있습니다.

2. Gemini는 availability가 약할 수 있음
- 현재 로컬 로그 샘플에서 `usageMetadata`를 아직 못 찾은 경우가 있습니다.

3. polling 부하
- launcher는 1초 polling이므로, token monitor는 TTL 캐시가 필요합니다.
- 현재 초안은 30초 캐시 기준이 적절합니다.

## 추천 후속 단계

1. Codex/Claude usage summary 안정화
2. Gemini sample 확보 후 parser 보강
3. `Quota:` 외에 세부 tooltip 또는 secondary line 검토
4. 필요 시 `Setup/Check`에 token source availability를 soft informational 항목으로 추가

## 장기 방향과 현재 범위 분리

현재 shipped 목표는 launcher UI의 local token visibility 보강입니다.

이 작업은:

- approval flow를 바꾸지 않고
- model runtime을 교체하지 않으며
- document-first MVP 범위를 넘지 않습니다.

장기적으로는 optional project-aware usage attribution, historical token timeline, per-agent capacity diagnostics로 확장할 수 있지만, 이번 1차 구현 범위에는 포함하지 않습니다.
