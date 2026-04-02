# 파이프라인 디스패치 통합 정리 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 5개 패치로 누적된 파이프라인 디스패치 코드를 안정적인 단일 구현으로 정리

**Architecture:** tmux_send_keys를 pane 타입 인자 기반으로 리팩터, dead pane 자동 복구, activity 상태 영속화

---

### Task 1: tmux_send_keys에 pane_type 파라미터 추가 + heuristic 제거

**Files:**
- Modify: `watcher_core.py` (tmux_send_keys 함수)

- [ ] **Step 1: tmux_send_keys 시그니처 변경**

```python
def tmux_send_keys(pane_target: str, command: str, dry_run: bool = False, pane_type: str = "claude") -> bool:
```

`is_codex` heuristic 전체 제거. `pane_type == "codex"`로 분기.

- [ ] **Step 2: StateMachine 호출부 수정**

verify dispatch → `pane_type="codex"`, claude dispatch → `pane_type="claude"`

- [ ] **Step 3: 테스트 — `python3 -m py_compile watcher_core.py`**

- [ ] **Step 4: 커밋**

---

### Task 2: dead pane 감지 + respawn-pane 자동 복구

**Files:**
- Modify: `watcher_core.py` (tmux_send_keys 내부)

- [ ] **Step 1: dead pane 감지 함수 추가**

```python
def _is_pane_dead(pane_target: str) -> bool:
    try:
        result = subprocess.run(
            ["tmux", "display-message", "-t", pane_target, "-p", "#{pane_dead}"],
            check=True, capture_output=True, text=True,
        )
        return result.stdout.strip() == "1"
    except subprocess.CalledProcessError:
        return True
```

- [ ] **Step 2: tmux_send_keys에서 dead pane이면 respawn**

Codex pane이 dead면 `tmux respawn-pane -k -t PANE` 후 bash 복구 → codex 실행.

- [ ] **Step 3: 테스트 — syntax check + start-pipeline.sh로 실제 테스트**

- [ ] **Step 4: 커밋**

---

### Task 3: activity 상태를 JobState 필드로 영속화

**Files:**
- Modify: `watcher_core.py` (JobState dataclass + _handle_verify_running)

- [ ] **Step 1: JobState에 필드 추가**

```python
@dataclass
class JobState:
    ...
    last_pane_snapshot: str = ""
    last_activity_at: float = 0.0
```

- [ ] **Step 2: _handle_verify_running에서 동적 attr 대신 필드 사용**

`job._last_pane_snapshot` → `job.last_pane_snapshot`
`job._last_activity_at` → `job.last_activity_at`

- [ ] **Step 3: job.save()에서 자동 영속화 확인 (asdict 사용하므로 OK)**

- [ ] **Step 4: 커밋**

---

### Task 4: temp file cleanup을 atexit + cleanup list로 변경

**Files:**
- Modify: `watcher_core.py`

- [ ] **Step 1: 모듈 레벨 cleanup 리스트 + atexit 등록**

```python
import atexit
_prompt_files_to_clean: list[str] = []

def _cleanup_prompt_files():
    for path in _prompt_files_to_clean:
        try: os.unlink(path)
        except OSError: pass

atexit.register(_cleanup_prompt_files)
```

- [ ] **Step 2: tmux_send_keys에서 daemon thread 제거, cleanup list에 추가**

- [ ] **Step 3: import를 모듈 상단으로 이동 (tempfile, os)**

- [ ] **Step 4: 커밋**

---

### Task 5: shell 스크립트 pane ID 통일 + STATUS 체크 통일

**Files:**
- Modify: `pipeline-watcher-v3.sh`
- Modify: `pipeline-watcher-v3-logged.sh`
- Delete: `pipeline-watcher-tmux.sh` (deprecated)

- [ ] **Step 1: v3, v3-logged에서 pane 타겟을 인자로 받도록 변경**

```bash
PANE_CLAUDE="${2:-$SESSION:0.0}"
PANE_CODEX="${3:-$SESSION:0.1}"
```

- [ ] **Step 2: v3-logged에 STATUS 체크 로직 추가 (v3에서 복사)**

- [ ] **Step 3: pipeline-watcher-tmux.sh 삭제, stop-pipeline.sh에서 참조 제거**

- [ ] **Step 4: 커밋**

---

### Task 6: 최종 검증

- [ ] **Step 1: `bash -n` 모든 shell 스크립트**
- [ ] **Step 2: `python3 -m py_compile watcher_core.py`**
- [ ] **Step 3: start-pipeline → Codex dispatch → 정상 작동 확인**
- [ ] **Step 4: Codex 작업 완료 후 pane dead → 재dispatch 확인**
- [ ] **Step 5: 최종 커밋 + 푸시**
