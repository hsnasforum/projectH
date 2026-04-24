# 2026-04-24 M28 마일스톤 선택 자문

## 배경
- PR #32 머지 이후 M27 Axes 1-2와 다수의 인프라 슬라이스가 배포되었습니다.
- 사용자 메모리(`project_current_phase.md`)에서 "기능은 충분하나 구조가 따라오지 못하는 단계"임을 명시하며 기능 추가 보류를 요청했습니다.
- 현재 `feat/watcher-turn-state` 브랜치에 runtime/supervisor/watcher 구조 개선 중심의 uncommitted changes가 존재합니다.

## 판단 근거
1. **사용자 의도 부합**: 구조적 안정성 확보를 우선시하는 사용자의 최근 피드백과 일치합니다.
2. **리스크 감소**: `verify close chain`, `lease release`, `active_round selection` 3축이 현재 임시 패치 형태로 유지되고 있어, 이를 structural bundle로 정리하는 것이 향후 incident 예방에 필수적입니다.
3. **일관성**: 이번 라운드의 uncommitted changes가 이미 구조 개선을 향하고 있으므로, 이를 수용하고 공식화하는 것이 자연스러운 흐름입니다.

## 권고 사항
- **Option A — Structural owner bundle**을 선택합니다.
- 다음 단계로 `verify close chain contract` 문서화(Axis 1)를 위한 `implement_handoff`를 진행할 것을 권장합니다.
- uncommitted changes를 먼저 커밋하여 M28 작업의 베이스라인을 명확히 해야 합니다.
