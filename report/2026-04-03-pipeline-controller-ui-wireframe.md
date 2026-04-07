# Pipeline Controller UI — 1단계 와이어프레임 설계

**작성일**: 2026-04-03  
**성격**: 내부용 controller UI 기획 + 와이어프레임  
**전제**: tmux 백엔드 유지, 그 위에 얹는 운영 가시성/제어 UI

---

## 1. 제품 목표 요약

사용자가 WSL/tmux 창을 직접 다루지 않고, **하나의 앱 화면에서 3-agent 파이프라인의 상태를 보고, 시작/중지하고, 각 agent에 입력할 수 있게** 하는 내부용 controller입니다.

핵심 가치:
- **운영 가시성**: 현재 라운드가 어떤 단계인지 한눈에 파악
- **제어성**: 시작/중지/재시작/개입을 UI에서 수행
- **안전성**: `needs_operator`가 Claude에게 잘못 전달되는 구조를 UI 레벨에서 방지
- **점진적 독립**: 초기에는 tmux pane 미러링, 장기적으로는 tmux를 숨기고 독자 터미널 UI로 발전

비목표 (1단계 제외):
- 예쁜 디자인, 외부 사용자용 UI
- projectH 문서 비서 본체 UI와의 통합
- agent 추가/삭제 동적 관리

---

## 2. 사용자 시나리오

### 시나리오 1: 아침에 파이프라인 시작
사용자가 앱을 열면 "프로젝트: projectH" + "파이프라인: 중지됨"이 보입니다. "시작" 버튼을 누르면 3개 agent가 차례로 뜨고, 각 pane에 CLI 초기화 과정이 보입니다. 초기화가 끝나면 "Claude: idle / Codex: idle / Gemini: idle"로 바뀌며, watcher가 첫 턴을 판단해서 적절한 agent에 프롬프트를 보냅니다. (초기화 시간은 agent별로 다르며, watcher의 startup-grace와 readiness 체크에 의해 결정됩니다.)

### 시나리오 2: 작업 중 모니터링
Claude가 코드를 작성하고 있는 동안, 사용자는 중앙 패널에서 Claude pane의 실시간 출력을 봅니다. 우측 상태 패널에는 "현재 라운드: Claude 구현 중 / 근거: work/4/3/...md" 가 표시됩니다. Claude가 `/work` closeout을 남기면, 상태가 자동으로 "Codex 검수 대기"로 바뀝니다.

### 시나리오 3: Codex → Gemini 에스컬레이션
Codex가 다음 슬라이스를 못 정해서 `.pipeline/gemini_request.md`를 작성하면, 상태 패널이 "Gemini 자문 요청됨"으로 바뀌고 Gemini pane이 자동으로 포커스됩니다. Gemini가 advisory를 남기면 다시 Codex로 돌아옵니다.

### 시나리오 4: operator 개입 필요
`.pipeline/operator_request.md`가 생성되면, 상태 패널에 주황색 배너 "Operator 결정 필요"가 뜨고, 요청 내용이 요약 표시됩니다. 사용자가 결정을 내리면, Codex가 새 `claude_handoff.md` 또는 갱신된 control signal을 작성하여 `operator_request.md`보다 최신 상태가 되면 파이프라인이 재개됩니다. (operator_request를 직접 resolved로 바꾸는 것이 아니라, 더 최신 control signal이 생기면 자동 해제되는 구조입니다.)

### 시나리오 5: agent 하나가 죽음
Codex pane이 dead 상태가 되면, 해당 agent 카드에 빨간 "Dead" 배지가 뜨고 "재시작" 버튼이 나타납니다. 클릭하면 pane이 respawn되고 codex가 다시 시작됩니다.

---

## 3. 전체 화면 구조

```
┌────────────────────────────────────────────────────────────────────────┐
│  [Global Toolbar]                                                      │
│  projectH  ●  Pipeline: Running  │  ▶ Start  ■ Stop  ↻ Restart       │
├──────────┬─────────────────────────────────────┬───────────────────────┤
│          │                                     │                       │
│ Control  │      3-Agent 화면 영역               │   Status / Handoff   │
│ Panel    │                                     │   Panel              │
│          │  ┌──────────┬──────────┬──────────┐ │                       │
│ Project  │  │ Claude   │ Codex    │ Gemini   │ │  Round: #7           │
│ Agent    │  │ (impl)   │ (verify) │ (arb)    │ │  Phase: Codex 검수   │
│ Status   │  │          │          │          │ │                       │
│ Latest   │  │ [pane    │ [pane    │ [pane    │ │  Handoff Slots:      │
│ Files    │  │  mirror] │  mirror] │  mirror] │ │  ├ claude_handoff ✓  │
│          │  │          │          │          │ │  ├ gemini_request —  │
│          │  └──────────┴──────────┴──────────┘ │  ├ gemini_advice —   │
│          │                                     │  └ operator_req —    │
│          │                                     │                       │
├──────────┴─────────────────────────────────────┴───────────────────────┤
│  [Command Input]                                                       │
│  대상: [Claude ▼]  │ 메시지 입력...                    │ [전송] [개입] │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. 화면별 와이어프레임 설명

### 4-A. Global Toolbar

```
┌────────────────────────────────────────────────────────────────────────┐
│  🔵 projectH                        Pipeline: ● Running    elapsed 12m│
│  [▶ Start] [■ Stop] [↻ Restart]     Mode: experimental     watcher ✓ │
└────────────────────────────────────────────────────────────────────────┘
```

**목적**: 파이프라인 전체 상태를 한 줄로 요약하고 시작/중지 제어를 제공합니다.

**표시 정보**:
- 프로젝트명
- 파이프라인 상태 (Running / Stopped / Error)
- 경과 시간
- 실행 모드 (experimental / baseline / both)
- watcher 생존 여부 (✓ alive / ✗ dead)

**우선순위**: 항상 최상단 고정, 모든 상태에서 표시됩니다.

### 4-B. 3-Agent 화면 영역 (중앙)

**기본 레이아웃**: 3열 균등 분할 (Claude | Codex | Gemini)

```
┌─────────────────────┬─────────────────────┬─────────────────────┐
│ ● Claude (impl)     │ ◉ Codex (verify)    │ ○ Gemini (arb)      │
│ Status: Working     │ Status: Idle        │ Status: Idle        │
│ ─────────────────── │ ─────────────────── │ ─────────────────── │
│                     │                     │                     │
│ • Reading CLAUDE.md │ > _                 │ > _                 │
│ • Explored          │                     │                     │
│   └ Read file.py    │                     │                     │
│ • Writing code...   │                     │                     │
│                     │                     │                     │
│ ─────────────────── │ ─────────────────── │ ─────────────────── │
│ gpt-5.4 · 68% left  │ gpt-5.4 · 92% left  │ gemini-2.5 · 100%   │
└─────────────────────┴─────────────────────┴─────────────────────┘
```

**상호작용**:
- 각 agent 헤더 클릭 → 해당 pane 확대 모드 (전체 폭 사용)
- 확대 모드에서 다시 클릭 → 3열로 복귀
- Esc → 3열 복귀

**Agent 카드 헤더 정보**:
- 상태 인디케이터: ● Working (녹색) / ◉ Idle (파란색) / ○ Standby (회색) / ✗ Dead (빨간색)
- 역할 라벨: impl / verify / arb
- 마지막 동작 시각

**pane 미러링 전략**:
- tmux pane의 출력을 주기적(0.5초)으로 `tmux capture-pane`으로 읽어서 표시합니다.
- TUI redraw 문제 완화: 전체 pane 텍스트를 `<pre>` 블록으로 표시하되, ANSI color code는 HTML color로 변환합니다.
- 스크롤 위치는 기본적으로 bottom-follow (최신 출력 추적)이며, 사용자가 위로 스크롤하면 follow가 일시 해제됩니다.
- 매우 긴 출력은 최근 200줄만 표시하고 "더 보기"로 전체 확인할 수 있습니다.

**UI 상태 카드 분리 항목** (pane 텍스트와 별도로 추출):
- `• Working` / `• Explored` / `• Ran` 같은 Codex 진행 상태 → 상태 배지로 추출
- `Worked for Xm Ys` → 경과 시간 표시
- `gpt-5.4 xhigh · 68% left` → 토큰 잔량 바로 추출
- Claude의 `> ` 프롬프트 대기 → Idle 상태로 전환

### 4-C. Control Panel (좌측)

```
┌──────────────────┐
│ 📁 프로젝트       │
│   projectH       │
│   ~/code/projectH│
│                  │
│ 🔧 Agent 상태     │
│  Claude   ● busy │
│  Codex    ◉ idle │
│  Gemini   ○ off  │
│                  │
│ 📊 현재 라운드     │
│  #7 — Codex 검수 │
│                  │
│ 📄 최신 파일       │
│  work: ...clamp  │
│    (2분 전)      │
│  verify: ...reg  │
│    (5분 전)      │
│                  │
│ 🔌 Watcher       │
│  PID: 241079 ✓   │
│  poll: 1.0s      │
│  uptime: 32m     │
└──────────────────┘
```

**목적**: 프로젝트 정보, agent 상태 요약, 현재 라운드 단계, 최신 파일 경로를 한 곳에 모읍니다.

**표시 정보 상세**:
- **프로젝트 선택**: 1단계에서는 고정 (향후 드롭다운으로 확장 가능하도록 placeholder)
- **Agent 상태**: 각 agent의 이름, 역할, 현재 상태 (busy/idle/off/dead)
  - 클릭 시 해당 agent pane으로 포커스 이동
- **현재 라운드**: 라운드 번호 + 현재 단계 (Claude 구현 / Codex 검수 / Gemini 자문 / Operator 대기)
- **최신 파일**: `work/`와 `verify/`의 최신 .md 파일명과 수정 시각
- **Watcher 상태**: PID, alive 여부, poll 간격, uptime

### 4-D. Handoff / State Panel (우측)

```
┌──────────────────────┐
│ 📋 Handoff 상태       │
│                      │
│ ┌ claude_handoff.md  │
│ │ STATUS: implement  │
│ │ slice: "add ..."   │
│ │ 수정: 3분 전        │
│ └ [열기]             │
│                      │
│ ┌ gemini_request.md  │
│ │ (없음)             │
│ └                    │
│                      │
│ ┌ gemini_advice.md   │
│ │ (없음)             │
│ └                    │
│                      │
│ ┌ operator_request   │
│ │ (없음)             │
│ └                    │
│                      │
│ ── 라운드 흐름 ──     │
│                      │
│  Claude ──→ work/    │
│    ↓                 │
│  Codex  ──→ verify/  │
│    ↓                 │
│  ◉ handoff 작성 대기  │
│    ↓                 │
│  Claude (다음 라운드) │
│                      │
│ ── 최근 로그 ──       │
│ 01:38 Codex dispatch │
│ 01:34 Claude done    │
│ 01:31 Codex done     │
└──────────────────────┘
```

**목적**: `.pipeline/` 하위의 4개 canonical 슬롯 상태를 시각화하고, 현재 라운드 흐름을 다이어그램으로 보여줍니다.

**슬롯별 표시**:
- 파일 존재 여부, STATUS 값, 주요 내용 1줄 요약, 수정 시각
- "열기" 버튼 → 파일 내용 전체를 모달로 표시
- 파일이 없으면 "(없음)" 회색 표시

**라운드 흐름 다이어그램**:
- 현재 단계에 ◉ 포인터 표시
- 정상 흐름: Claude → work → Codex → verify → handoff → Claude
- Gemini 분기: Codex → gemini_request → Gemini → gemini_advice → Codex
- Operator 분기: → operator_request → (대기)

**최근 로그**: watcher.log에서 최근 10건의 이벤트를 역순으로 표시합니다.

### 4-E. Command Input (하단)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 대상: [◉ Claude ▼]  │ 메시지를 입력하세요...              │ [전송]    │
│                     │                                    │ [개입]    │
│ ○ Direct Send       │                                    │ [메모]    │
│ ○ Interrupt                                                          │
│ ○ Note Only                                                          │
└────────────────────────────────────────────────────────────────────────┘
```

**목적**: 각 agent에게 메시지를 보내거나, operator 개입을 수행합니다.

**대상 선택**: 드롭다운으로 Claude / Codex / Gemini / Operator 선택

**행동 구분**:
- **Direct Send**: 선택한 agent pane에 텍스트를 직접 전송 (paste-buffer + Enter)
- **Interrupt**: 해당 agent에 Ctrl+C를 보내고 메시지를 전송
- **Note Only**: `.pipeline/operator_request.md`에 기록만 남기고 agent에 전송하지 않음

**Operator 전용 입력**: 대상이 "Operator"일 때는 `operator_request.md`의 결정을 입력하는 전용 UI로 전환됩니다:
```
┌────────────────────────────────────────────────────────────────────────┐
│ 🔶 Operator 결정 입력                                                  │
│                                                                        │
│ 요청: "same-family improvement vs new quality axis 중 선택 필요"        │
│                                                                        │
│ 결정: [                                                    ] [확인]    │
│                                                                        │
│ → operator 결정을 기록하고, Codex가 새 control signal을 작성하면 해제   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 5. 컴포넌트 목록

| 컴포넌트 | 위치 | 역할 |
|----------|------|------|
| `GlobalToolbar` | 상단 | 파이프라인 상태 요약 + 시작/중지/재시작 |
| `ControlPanel` | 좌측 | 프로젝트 정보, agent 상태, 라운드, 최신 파일, watcher |
| `AgentPaneView` | 중앙 | tmux pane 미러링 (ANSI → HTML 변환) |
| `AgentHeader` | 중앙 상단 | agent 이름, 역할, 상태 배지, 확대 토글 |
| `HandoffPanel` | 우측 | 4개 슬롯 상태 카드 + 라운드 흐름 다이어그램 |
| `RoundFlowDiagram` | 우측 | 현재 단계 시각화 (세로 흐름도) |
| `EventLog` | 우측 하단 | watcher.log 최근 이벤트 |
| `CommandInput` | 하단 | 대상 선택 + 메시지 입력 + 행동 선택 |
| `OperatorDecisionModal` | 모달 | operator_request 결정 입력 전용 |
| `FilePreviewModal` | 모달 | handoff/request 파일 전체 내용 보기 |
| `ErrorBanner` | 상단 오버레이 | 에러/경고 배너 (agent dead, watcher down 등) |

---

## 6. 상태 전이

### 6.1 앱 실행 전

```
화면: "프로젝트를 선택하세요" + 경로 입력
Toolbar: Pipeline: — (비활성)
Agent 영역: 빈 화면
Control Panel: 프로젝트 경로만 입력 가능
```

### 6.2 프로젝트 선택됨

```
화면: "파이프라인이 중지되어 있습니다. [시작] 버튼을 눌러주세요."
Toolbar: Pipeline: Stopped ■
Control Panel: 프로젝트 정보 표시, agent 상태 모두 "off"
Agent 영역: 3개 빈 pane placeholder
```

### 6.3 Pipeline 시작됨

```
Toolbar: Pipeline: Starting... (스피너)
Agent 영역: 각 pane에 CLI 초기화 출력
Control Panel: agent 상태 → "starting..."
→ CLI 초기화 완료 후: agent 상태 → "idle"
→ watcher 시작 후: Watcher: ✓ alive
```

### 6.4 Claude 작업 중

```
Agent Claude: ● Working (녹색)
Agent Codex: ◉ Idle (파란색)
Agent Gemini: ○ Standby (회색)
라운드 흐름: ◉ Claude 구현 중
Handoff Panel: claude_handoff.md — STATUS: implement 표시
```

### 6.5 Codex 검수 중

```
Agent Claude: ◉ Idle
Agent Codex: ● Working (녹색)
Agent Gemini: ○ Standby
라운드 흐름: ◉ Codex 검수 중
최신 파일: work/ 최신 갱신됨
```

### 6.6 Gemini Arbitration 중

```
Agent Claude: ◉ Idle
Agent Codex: ◉ Idle (자문 결과 대기)
Agent Gemini: ● Working (녹색)
라운드 흐름: ◉ Gemini 자문 중
Handoff Panel: gemini_request.md — STATUS: request_open
```

### 6.7 Operator 결정 대기

```
Toolbar: 🔶 Operator Decision Required (주황 배너)
모든 Agent: ◉ Idle (자동 진행 중단)
라운드 흐름: ◉ Operator 결정 대기
Handoff Panel: operator_request.md — STATUS: needs_operator (주황 하이라이트)
하단 입력: Operator 결정 입력 모드로 자동 전환
```

### 6.8 Pipeline 중지

```
Toolbar: Pipeline: Stopped ■
Agent 영역: 모든 pane "중지됨" 오버레이
Control Panel: agent 상태 모두 "off"
Watcher: ✗ stopped
```

---

## 7. 주요 상호작용

| 행동 | 트리거 | 결과 |
|------|--------|------|
| 파이프라인 시작 | [▶ Start] 클릭 | `bash start-pipeline.sh <selected_project> --mode experimental` 실행 |
| 파이프라인 중지 | [■ Stop] 클릭 | `bash stop-pipeline.sh .` 실행 |
| 파이프라인 재시작 | [↻ Restart] 클릭 | stop → start 순차 실행 |
| Agent pane 확대 | 헤더 클릭 | 3열 → 1열 전환, 해당 pane만 표시 |
| Agent에 메시지 전송 | 하단 입력 + [전송] | `tmux send-keys` 또는 `paste-buffer` |
| Agent 인터럽트 | 하단 입력 + [개입] | `tmux send-keys C-c` + 메시지 |
| Operator 결정 입력 | Operator 모드에서 [확인] | operator 결정 기록 → Codex가 새 control signal 작성 시 해제 |
| Handoff 파일 보기 | [열기] 클릭 | 모달에 파일 전체 내용 표시 |
| Dead pane 재시작 | [재시작] 클릭 | `tmux respawn-pane` + CLI 재실행 |

---

## 8. 에러/예외 상태

### 8.1 CLI 미설치

```
┌──────────────────────────────────────────────────┐
│ ⚠️ claude CLI가 설치되어 있지 않습니다             │
│                                                  │
│ 설치: npm install -g @anthropic-ai/claude-code    │
│                                        [확인]    │
└──────────────────────────────────────────────────┘
```

시작 전에 `which claude`, `which codex`, `which gemini`로 체크합니다. 없으면 설치 안내를 표시하고 시작을 차단합니다.

### 8.2 로그인 안 됨

```
┌──────────────────────────────────────────────────┐
│ ⚠️ Codex 로그인이 필요합니다                       │
│                                                  │
│ 터미널에서 `codex login`을 실행해주세요             │
│                                        [확인]    │
└──────────────────────────────────────────────────┘
```

pane 출력에서 "login" 또는 "authentication" 키워드를 감지하면 표시합니다.

### 8.3 tmux 세션 없음

```
Toolbar: Pipeline: ✗ No tmux session
[▶ Start] 버튼만 활성화
나머지: 비활성 오버레이
```

`tmux ls` 결과에 세션이 없으면 이 상태가 됩니다.

### 8.4 Watcher 죽음

```
┌──────────────────────────────────────────────────┐
│ 🔴 Watcher가 종료되었습니다 (PID: 241079)          │
│                                                  │
│ Agent는 살아있지만 자동 전환이 중단됩니다            │
│                              [Watcher 재시작]    │
└──────────────────────────────────────────────────┘
```

watcher PID를 주기적으로 체크하고, 죽으면 배너를 표시합니다. [Watcher 재시작] 클릭 시 `watcher_core.py`를 다시 실행합니다.

### 8.5 Handoff 파일 불일치

```
┌──────────────────────────────────────────────────┐
│ ⚠️ claude_handoff.md에 STATUS가 없습니다           │
│                                                  │
│ 파일 내용을 확인해주세요                            │
│                         [파일 보기] [무시]         │
└──────────────────────────────────────────────────┘
```

STATUS 파싱 실패 시 표시합니다.

### 8.6 Agent Pane Freeze

```
Agent 카드:
│ ● Codex (verify)     │
│ Status: Frozen (5m)  │
│ ⚠️ 출력 없음 5분 이상  │
│      [Ctrl+C] [재시작]│
```

pane 출력이 5분 이상 변하지 않으면 "Frozen" 상태로 표시하고 대응 버튼을 제공합니다.

### 8.7 operator_request 발생

```
Toolbar에 주황 배너: "🔶 Operator 결정이 필요합니다"
하단 입력이 자동으로 Operator 모드로 전환
모든 agent 자동 진행 중단
```

이 상태에서 사용자가 결정을 입력하지 않으면 파이프라인은 멈춰 있습니다.

---

## 9. 1단계 범위 / 제외 범위

### 포함 (1단계)

- Global Toolbar (시작/중지/재시작)
- 3-Agent pane 미러링 (tmux capture-pane 기반)
- Control Panel (agent 상태, 최신 파일, watcher 상태)
- Handoff Panel (4개 슬롯 상태 표시)
- Command Input (대상 선택 + 전송)
- 기본 에러 배너 (dead pane, watcher down)
- Operator 결정 입력 UI

### 제외 (1단계에서 빠지는 것)

- 프로젝트 동적 선택/전환
- Agent 추가/삭제/교체
- 권한 프로필 관리 (Restricted / Workspace Write / Full Access)
- 로그 검색/필터
- 라운드 히스토리 타임라인
- 성능 대시보드 (토큰 사용량 추이 등)
- 모바일/태블릿 대응
- 다크모드 (controller UI용)

---

## 10. 2단계, 3단계 확장 방향

### 2단계: 운영 편의성

- **프로젝트 선택**: 드롭다운으로 여러 프로젝트 전환
- **라운드 히스토리**: 과거 라운드의 work → verify → handoff 흐름을 타임라인으로 표시
- **로그 뷰어**: watcher.log를 검색/필터할 수 있는 전용 패널
- **Diff 뷰어**: work/verify 파일의 변경 사항을 인라인 diff로 표시
- **알림**: 브라우저 Notification API로 operator_request, agent dead 알림

### 3단계: tmux 독립

- **자체 터미널 에뮬레이터**: tmux pane 대신 xterm.js 등을 사용하여 각 agent의 PTY를 직접 관리
- **Agent 동적 관리**: UI에서 agent 추가 (예: Grok CLI), 역할 할당, 권한 프로필 설정
- **Role 기반 확장**: agent 이름이 아닌 role (implementer / verifier / arbiter) 기반으로 설정
  - 설정 화면에서 "implementer = Claude" → "implementer = Grok"으로 변경 가능
- **권한 프로필**: Restricted (읽기만) / Workspace Write (코드 수정 허용) / Full Access (네트워크 포함)
- **멀티 프로젝트 동시 운영**: 탭으로 여러 프로젝트 파이프라인 동시 모니터링

### Role 기반 확장 설계 (placeholder)

1단계에서는 Claude/Codex/Gemini를 하드코딩하되, 내부 데이터 구조에서는 role 기반으로 설계합니다:

```
// 1단계 내부 구조 (향후 설정 파일로 분리)
agents = [
  { role: "implementer", cli: "claude", flags: "--dangerously-skip-permissions" },
  { role: "verifier",    cli: "codex",  flags: "--ask-for-approval never --disable apps" },
  { role: "arbiter",     cli: "gemini", flags: "--approval-mode auto_edit" },
]
```

이렇게 하면 나중에 agent 교체 시 설정만 바꾸면 됩니다.

---

## 부록: 기술 구현 메모 (1단계)

### 백엔드 통신

- **파이프라인 제어**: `child_process.exec("bash start-pipeline.sh ...")`
- **pane 미러링**: 0.5초마다 `tmux capture-pane -pt PANE_ID` 실행, 결과를 WebSocket으로 프론트에 전달
- **상태 감시**: 1초마다 `.pipeline/` 하위 파일의 mtime + 내용을 체크
- **watcher 상태**: `/proc/PID/status` 또는 `kill -0 PID`로 생존 체크

### 프론트엔드

- React + Tailwind (기존 projectH 프론트와 동일 스택)
- 별도 라우트 `/controller` 또는 독립 앱
- WebSocket으로 pane 출력 + 상태 업데이트 수신

### ANSI → HTML 변환

- `ansi-to-html` npm 패키지 또는 경량 자체 구현
- 색상, 볼드, 언더라인만 지원 (커서 이동 등 제어 문자는 무시)
- 성능: 최근 200줄만 변환, 나머지는 스크롤 시 lazy 변환

---

*이 문서는 코드 구현 없이 와이어프레임/기획만 정리한 것입니다. 실제 구현은 이 설계를 기반으로 별도 계획을 작성한 뒤 진행합니다.*
