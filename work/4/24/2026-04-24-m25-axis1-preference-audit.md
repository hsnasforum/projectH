# 2026-04-24 M25 Axis 1 preference lifecycle audit

## 변경 파일
- `app/handlers/preferences.py`
- `app/web.py`
- `app/frontend/src/api/client.ts`
- `app/frontend/src/components/PreferencePanel.tsx`
- `tests/test_preference_handler.py`
- `docs/MILESTONES.md`
- `work/4/24/2026-04-24-m25-axis1-preference-audit.md`

## 사용 skill
- `doc-sync`: M25 정의와 Axis 1 shipped entry를 현재 구현 사실에 맞춰 `docs/MILESTONES.md`에 반영했습니다.
- `finalize-lite`: handoff acceptance에 적힌 검증만 좁게 실행하고 `/work` closeout을 실제 결과 기준으로 정리했습니다.

## 변경 이유
- 이번 라운드는 council convergence 기반 handoff `CONTROL_SEQ: 102`로, preference lifecycle의 aggregate 상태를 한눈에 볼 수 있는 read-only audit 표면을 추가하는 M25 Axis 1 slice입니다.
- `list_preferences_payload()`는 각 preference별 `conflict_info`를 계산하고 있었지만, 상태별 개수나 전체 conflict pair 수를 묶어 보는 aggregate endpoint가 없어서 현재 lifecycle health를 빠르게 확인하기 어려웠습니다.
- 이번 변경은 mutation 없이 `GET /api/preferences/audit`로 집계치를 노출하고, 기존 `PreferencePanel` 위에 compact summary line만 추가하는 bounded API + UI slice입니다.

## 핵심 변경
- `app/handlers/preferences.py`
  - `get_preference_audit()`를 추가했습니다.
  - `self.preference_store.list_all()` 기준으로 `total`, `by_status`, `conflict_pair_count`를 집계합니다.
  - conflict pair 계산은 기존 `_jaccard_word_similarity > 0.7` 기준을 재사용합니다.
- `app/web.py`
  - `GET /api/preferences/audit`를 추가했습니다.
  - 새 mixin 인스턴스를 만들지 않고 기존 `/api/preferences`와 같은 패턴으로 `self.server.service.get_preference_audit()`를 호출하도록 연결했습니다.
- `app/frontend/src/api/client.ts`
  - `PreferenceAudit` 타입과 `fetchPreferenceAudit()`를 추가했습니다.
- `app/frontend/src/components/PreferencePanel.tsx`
  - 기존 `load()` 흐름 안에서 preference 목록과 audit 요약을 함께 불러오도록 했습니다.
  - preference list 위에 `활성 N · 후보 M · 충돌 K쌍` 형식의 compact summary line을 추가했습니다.
  - 별도 audit panel은 만들지 않았고, 기존 panel 구조 안에서 한 줄만 노출합니다.
- `tests/test_preference_handler.py`
  - `get_preference_audit()`가 `total`, `by_status`, `conflict_pair_count`를 올바르게 반환하는 신규 테스트 1건을 추가했습니다.
- `docs/MILESTONES.md`
  - `Milestone 25: Preference Lifecycle Audit` 정의와 Axis 1 shipped entry를 추가했습니다.

## 검증
- `python3 -m py_compile app/handlers/preferences.py app/web.py`
  - 통과: 출력 없음
- `python3 -m unittest tests.test_preference_handler -v`
  - 통과: `Ran 6 tests`, `OK`
  - 신규 테스트 포함:
    - `test_get_preference_audit_returns_counts`
- `cd app/frontend && npx tsc --noEmit`
  - 통과: 출력 없음
- `git diff --check -- app/handlers/preferences.py app/web.py app/frontend/src/api/client.ts app/frontend/src/components/PreferencePanel.tsx tests/test_preference_handler.py docs/MILESTONES.md`
  - 통과: 출력 없음

## 남은 리스크
- 이번 라운드는 handoff 경계에 따라 handler 단위 테스트와 TypeScript 컴파일만 실행했고, Playwright/browser E2E는 추가하지 않았습니다. panel summary의 실제 브라우저 렌더링 회귀 확인은 M25 Axis 2 이상에서 다뤄야 합니다.
- `PreferencePanel`은 visible preference 목록에서 `rejected`를 숨기지만, audit endpoint는 store `list_all()` 전체를 집계합니다. 현재 handoff 의도상 맞는 동작이지만, 향후 UI 문구가 전체 기준인지 visible 기준인지 더 명확히 다듬을 여지는 있습니다.
- 작업 시작 시점에 이미 존재하던 unrelated untracked 상태(`report/gemini/2026-04-23-m20-closure-consolidation.md`, `report/gemini/2026-04-23-m21-axis2-reject-scope.md`, `report/gemini/2026-04-23-m21-definition.md`, `report/gemini/2026-04-23-m22-scope-definition.md`)는 건드리지 않았습니다.
