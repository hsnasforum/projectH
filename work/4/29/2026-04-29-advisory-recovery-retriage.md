# 2026-04-29 Advisory Recovery Full Bundle — retriage commit/push

## 이번 라운드 변경 파일

### 이번 라운드 직접 편집 (operator_retriage CONTROL_SEQ 1429)
- `verify/4/29/2026-04-29-advisory-recovery-retriage.md` — 신규 (retriage verify 노트)
- `work/4/29/2026-04-29-advisory-recovery-retriage.md` — 신규 (본 closeout)
- `.pipeline/operator_request.md` → 다음 컨트롤로 교체 예정 (CONTROL_SEQ 1430)

### 이번 라운드 커밋 산출물

**커밋 1** (이전 implement 라운드): `71b256f` — `pipeline_runtime/lane_surface.py`, `watcher_core.py`, `tests/test_watcher_core.py`
**커밋 2** (이번 retriage 커밋): `939dcf8` — `watcher_core.py`, `watcher_prompt_assembly.py`, `tests/test_watcher_core.py`, `.pipeline/README.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`

## 커밋/푸시 결과

| 단계 | 결과 |
|------|------|
| 커밋 `939dcf8` | ✓ 6 files, 307 ins/3 del |
| `git push origin fix/advisory-recovery-pane-busy-age` | ✓ `71b256f..939dcf8` |
| PR #88 업데이트 | ✓ https://github.com/hsnasforum/projectH/pull/88 |

## safety_stop 해소 근거

CONTROL_SEQ 1429 `safety_stop` 조건: "pause Gemini advisory loop; loop guard 검토 완료까지 advisory 차단"

| guard | 커밋 |
|-------|------|
| `pane_text_busy_age_seconds()` 파서 + stale advisory pane busy age 이중 판정 | 71b256f |
| inactive advisory lane busy cancel guard (grace 후 Escape) | 939dcf8 |
| prompt order: inactive cancel → operator_retriage 승격 이전 실행 | 939dcf8 |
| advisory request supersede: 동일 request 재투입 방지 | 939dcf8 |
| recovery prompt: 같은 stale request 재오픈 금지 | 939dcf8 |

## 검증 결과 (retriage 재실행)

- 통과: `py_compile watcher_core.py watcher_prompt_assembly.py pipeline_runtime/lane_surface.py tests/test_watcher_core.py`
- 통과: `python3 -m unittest tests.test_watcher_core` — `Ran 212 tests in 9.136s, OK`
- 통과: `git diff --check` (dirty 파일 전체)

## 다음 상태

- `fix/advisory-recovery-pane-busy-age` 브랜치: HEAD `939dcf8`, PR #88 (base: feat/m96-bundle) 리뷰/머지 대기
- M88-M96 PR 스택 (#71-#86): 머지 게이트 대기
- Gemini M97 방향 (CONTROL_SEQ 1394): PR #71-#88 머지 우선 (Option C) 권고
- 다음 컨트롤: `operator_request.md` CONTROL_SEQ 1430 (`pr_merge_gate`)

## 남은 리스크

- PR #88 base(`feat/m96-bundle`)가 main에 머지되어야 PR #88 최종 리타겟 가능.
- PR 스택 머지 순서: #71 → ... → #86 → #88 순 권장.
- E2E smoke: watcher-only 변경으로 미실행.
