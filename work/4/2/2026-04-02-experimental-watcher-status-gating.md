# 2026-04-02 experimental watcher STATUS gating

## 변경 파일

- `watcher_core.py`

## 사용 skill

- `work-log-closeout`

## 변경 이유

- baseline shell watcher(`pipeline-watcher-v3-logged.sh`)는 이미 `STATUS: implement`일 때만 Claude pane에 notify하는 분기가 있었음
- experimental Python watcher(`watcher_core.py`)의 `_check_feedback_update`는 `codex_feedback.md` 시그니처 변경 시 STATUS를 확인하지 않고 무조건 Claude에 notify하고 있었음
- operator-loop reduction prompts family의 same-family current-risk reduction으로, 두 watcher의 동작 일관성을 맞추는 슬라이스

## 핵심 변경

- `_read_feedback_status()` 헬퍼 추가: `self.feedback_path`에서 첫 `STATUS:` 줄을 읽어 값 반환
- `_check_feedback_update()`에 STATUS 분기 추가: `implement`일 때만 `_notify_claude` 호출
- `needs_operator`, STATUS 미존재, 알 수 없는 STATUS일 때는 notify 건너뛰고 `claude_notify_skipped` 이벤트를 raw 로그에 기록
- 기존 prompt wording, shell watcher 3개, `start-pipeline.sh`, 운영 문서, root docs는 미변경

## 검증

- `python3 -m py_compile watcher_core.py` — 통과 (출력 없음)
- `git diff --check -- watcher_core.py` — 통과 (whitespace 이슈 없음)
- `grep -n "STATUS\|feedback_updated\|notify_claude\|notify_skipped" watcher_core.py` — STATUS 분기, notify, skipped 로그 패턴 모두 확인

## 남은 리스크

- 런타임 통합 테스트(실제 tmux pane 환경에서 `needs_operator` feedback 전달 시 notify 차단 확인)는 미실행
- `_read_feedback_status()`는 파일 첫 `STATUS:` 줄만 읽으므로, 파일 중간에 다른 STATUS 줄이 있어도 무시됨 (baseline shell watcher와 동일 동작)
