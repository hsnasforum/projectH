# verify: 2026-05-22 watcher_core module-level fn extraction (A3 Step 1)

## 검증 결과: READY — 485개 통과

| 이동 | 출발 → 도착 | 확인 |
|---|---|---|
| `_line_looks_like_input_prompt` | watcher_core → lane_surface:135 | ✓ |
| `_pane_text_has_gemini_ready_prompt` | watcher_core → lane_surface | ✓ |
| `_prompt_cleanup_list`, `_cleanup_prompt_files` | watcher_core → watcher_prompt_assembly:22 | ✓ |
| `_write_prompt_file`, `_normalize_prompt_text` | watcher_core → watcher_prompt_assembly | ✓ |
| `_session_name_for_project` | 중복 제거 → alias import | ✓ |

watcher_core.py: 4498 → 4430줄 (net −68). WatcherCore 클래스 내부 변경 없음.
