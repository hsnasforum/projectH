# 2026-04-25 M30 milestones doc sync

## 변경 파일
- `docs/MILESTONES.md`
- `work/4/25/2026-04-25-m30-milestones-doc-sync.md`

## 사용 skill
- `doc-sync`: M30 Axes 1–3 완료 상태를 현재 milestone 문서에 맞추기 위해 사용했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행한 검증, 남은 리스크를 `/work` closeout으로 남기기 위해 사용했습니다.

## 변경 이유
- `CONTROL_SEQ: 145` implement handoff에 따라 M30 Axes 1–3 완료 기록이 `docs/MILESTONES.md`에 없던 drift를 정리해야 했습니다.
- M30 완료 이후 "Next 3 Implementation Priorities"가 여전히 M30 방향 선정 이전 상태를 가리키고 있어 PR #33, M31 방향, `watcher_signals.py` 중복 메모로 갱신했습니다.

## 핵심 변경
- `docs/MILESTONES.md`의 Milestone 29 다음에 `Milestone 30: Watcher Core Structural Decomposition` 섹션을 추가했습니다.
- M30 guardrail로 `pipeline_runtime/` 미수정, 기존 `tests/test_watcher_core.py` 계약 유지, 보존 함수 4개 미수정을 기록했습니다.
- Axis 1–3 shipped infrastructure를 seq 136–145 범위로 기록하고, M30 closed 상태를 명시했습니다.
- "Next 3 Implementation Priorities"를 PR #33 merge, M31 direction, `watcher_signals.py` prompt-line helper 중복 메모로 갱신했습니다.
- handoff 금지 범위에 따라 `PRODUCT_SPEC.md`, `ACCEPTANCE_CRITERIA.md`, `ARCHITECTURE.md`, `README.md` 등 다른 문서는 수정하지 않았습니다.

## 검증
- `sha256sum .pipeline/implement_handoff.md`
  - 통과: `6deb70a5cd9472129babb4db7d13ebbfb6498ba578aa7e80946c51542049380c`
- `python3 -m unittest tests.test_docs_sync -v 2>&1 | tail -5`
  - 통과: `Ran 13 tests`, `OK`
- `git diff --check -- docs/MILESTONES.md`
  - 통과: 출력 없음
- `grep -n "Milestone 30\|watcher_signals\|Axes 1–3" docs/MILESTONES.md | head -10`
  - 실행됨: 기존 앞쪽 `Axes 1–3` 항목이 많아 `head -10`에는 `Milestone 30`까지만 표시됐습니다.
- `grep -n "Milestone 30\|watcher_signals\|Axes 1–3" docs/MILESTONES.md | tail -10`
  - 통과: M30 shipped infrastructure, `watcher_signals.py`, M30 closed, Next priority duplication note가 확인됐습니다.

## 남은 리스크
- 이번 slice는 `docs/MILESTONES.md`만 갱신했습니다. handoff가 다른 docs 수정을 금지했으므로 plandoc/제품문서 추가 동기화는 수행하지 않았습니다.
- 작업 시작 전 `docs/MILESTONES.md`에는 M28/M29 섹션과 Next priority 갱신 등 기존 dirty 변경이 이미 있었습니다. 이번 closeout은 그 변경을 되돌리지 않고 M30 섹션 추가와 Next 3 항목 교체만 기록합니다.
