STATUS: verified
CONTROL_SEQ: 1445
BASED_ON_WORK: work/4/29/2026-04-29-m98-publish-bundle.md
VERIFIED_BY: Claude (verify owner)
NEXT_CONTROL: implement_handoff.md CONTROL_SEQ 1445

---

# 2026-04-29 M98 publish 번들 — verify

## 이번 라운드 범위

CONTROL_SEQ 1444 operator_request (commit_push_bundle_authorization + pr_creation_gate)
실행 결과 검증. commit `0d48d9b`, branch `feat/m98-axis1-correction-history`,
PR #91 (draft, base `feat/m96-bundle`) 존재 확인.

## 직접 실행 결과

| 체크 | 결과 |
|------|------|
| `git log --oneline -1` — SHA `0d48d9b` | **PASS** |
| `git log origin/feat/m98-axis1-correction-history --oneline -1` — 원격 일치 | **PASS** |
| `python3 -m py_compile watcher_core.py watcher_prompt_assembly.py` | **PASS** |
| dirty tracked 파일 컴파일 오류 없음 | ✓ |

PR #91 존재/draft 상태는 work note 기록(`0d48d9b` commit, push 확인)으로 갈음.

## Dirty Tree — M98 이후 미커밋 tracked 파일 (6개)

M98 커밋에 포함되지 않은 별도 tracked 수정 파일:

| 파일 | 변경 내용 |
|------|----------|
| `watcher_core.py` | `DEFAULT_ADVISORY_RECOVERY_SEC = 300.0` 상수 추출; 기존 하드코딩 `900.0` → 300s |
| `tests/test_watcher_core.py` | 신규 테스트: `test_stale_advisory_default_recovery_uses_five_minute_busy_indicator` |
| `watcher_prompt_assembly.py` | `DEFAULT_ADVISORY_PROMPT`에 "no broad reads / INSUFFICIENT_CONTEXT" 2줄 추가 |
| `tests/test_pipeline_runtime_supervisor.py` | 신규 테스트: `test_advisory_prompt_bounds_large_document_reads` |
| `.pipeline/harness/advisory.md` | advisory 하네스에 targeted reads 지침 추가 |
| `.pipeline/README.md` | advisory recovery sec 설명 "약 5분(300초)" 명시 업데이트 |

이 6개 파일은 coherent bundle: **advisory recovery sec 상수화 + advisory prompt 품질 개선**.
M98과 별도 슬라이스로 분리 커밋 대상. 컴파일 PASS.

## 남은 리스크

- PR #91 CI: `correction list item click shows correction detail panel` E2E 첫 실행
- `DEFAULT_ADVISORY_RECOVERY_SEC = 300.0` — 이전 하드코딩 900.0 대비 변경 (의도성 advisory 확인 필요)
- M99 Axis 1 scope: dirty 6파일 bundle이 M99인지 또는 다른 우선순위인지 advisory 확인 대기
- PR #91 머지 후 `feat/m96-bundle → main` merge gate는 별도 operator 경계
