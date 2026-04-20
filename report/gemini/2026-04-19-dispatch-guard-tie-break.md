# 2026-04-19 dispatch guard tie-break

## 상황
- `watcher_core.py`의 double-paste 리스크가 `prompt consumed` 상태를 성공으로 판정하도록 수정되어 해소됨.
- `tests/test_watcher_core.py`의 Codex dispatch confirmation 테스트가 통과하여 helper 수준의 경계가 확정됨.
- 현재 tree에는 `feat/watcher-turn-state` 브랜치 작업으로 인한 watcher, controller, runtime docs 쪽의 광범위한 수정 사항(dirty worktree)이 남아 있음.
- `MILESTONES.md`와 `docs/`는 internal pipeline을 release gate 외부의 도구로 정의하고 있으며, 핵심 목표는 Document Assistant MVP임.

## 판단
1. **리스크 해소:** 가장 시급했던 중복 입력 리스크가 검증되었으므로, 파이프라인의 안정성은 다음 라운드들을 수행하기에 충분한 수준임.
2. **우선순위 역전:** 내부 도구의 완성도를 높이는 작업(Priority 4: internal cleanup)보다 제품의 핵심 가치(Priority 2/3: user-visible improvement / new axis)로 복귀하는 것이 전략적으로 유리함.
3. **축 전환 필요성:** 현재의 dirty worktree를 계속 안고 파이프라인 고도화를 이어가기보다, Milestone 5(Grounded Brief)로 축을 전환하여 제품 로드맵과의 정합성을 맞출 시점임.

## 권고
- **RECOMMEND: close family and switch axis document-mvp**
- 파이프라인의 즉각적인 리스크가 해결되었으므로, 다음 슬라이스는 Grounded Brief와 Correction/Memory 계약을 다루는 제품 중심 작업으로 전환할 것을 권장함.
- 전환 시 현재의 dirty worktree 중 파이프라인 안정성에 필수적인 부분만 닫고, 나머지는 필요시 revert하거나 점진적으로 정리하며 제품 로드맵(Milestone 5)에 집중할 것.
