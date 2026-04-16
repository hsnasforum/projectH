# 2026-04-16 controller office browser-local toolbar preference persistence

## 변경 파일
- `controller/index.html`
- `tests/test_controller_server.py`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-office-toolbar-preference-persistence.md`

## 사용 skill
- 없음

## 변경 이유
- 이전 라운드에서 reduced-motion guard를 추가했지만, `_lowMotion`과 `AmbientAudio.muted` 모두 브라우저 새로고침 시 초기화되는 문제가 남아 있었습니다.
- `docs/superpowers/plans/2026-04-16-controller-office-view-projecth-adaptation.md`에서 browser-local persistence를 허용하고 있고, latest verify note에서도 refresh-reset을 남은 리스크로 기록했습니다.
- reduced-motion과 ambient mute를 별도 micro-round로 쪼개지 않고 하나의 coherent toolbar-preference slice로 묶었습니다.

## 핵심 변경
- `controller/index.html`
  - `toggleLowMotion()`에서 `localStorage.setItem('office_low_motion', ...)`으로 상태를 저장합니다.
  - low-motion 선언 직후 `localStorage.getItem('office_low_motion')`으로 복원하고 `_applyLowMotionUI()`로 버튼 UI를 동기화합니다.
  - `AmbientAudio.toggle()`에서 `localStorage.setItem('office_muted', ...)`으로 상태를 저장합니다.
  - BOOT 섹션에서 `localStorage.getItem('office_muted')`으로 muted 상태를 복원하고 버튼 아이콘/title을 반영합니다. audio 자동 재생은 하지 않습니다.
  - 모든 localStorage 접근은 `try/catch`로 감싸서 private browsing 등에서도 graceful fallback합니다.
- `tests/test_controller_server.py`
  - `test_controller_html_polls_runtime_api_only`에 persistence 계약 회귀 검증 4건을 추가했습니다:
    - `office_low_motion` storage key 존재
    - `office_muted` storage key 존재
    - `localStorage.setItem` 호출 존재
    - `localStorage.getItem` 호출 존재
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
  - reduced-motion 토글 절 뒤에 localStorage 키와 muted 복원 시 자동 재생 금지 계약을 추가했습니다.
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - reduced-motion/mute 운영 안내 뒤에 새로고침 후 유지 동작과 muted 복원 시 자동 재생 금지를 설명하는 항목을 추가했습니다.

## 검증
- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only`
  - 결과: `Ran 1 test in 0.002s`, `OK`
- `git diff --check -- controller/index.html tests/test_controller_server.py docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - 결과: 출력 없음 (whitespace 문제 없음)
- `tmp=$(mktemp --suffix=.js); trap 'rm -f "$tmp"' EXIT; sed -n '/<script>/,/<\/script>/p' controller/index.html | sed '1d;$d' > "$tmp"; node --check "$tmp"`
  - 결과: 출력 없음 (JS 구문 오류 없음)
- `rg -n "localStorage\\.(setItem|getItem)" controller/index.html`
  - 결과: `setItem` 2건(save), `getItem` 2건(restore) — backend route 없이 browser-local만 사용
- manual controller/browser smoke
  - 결과: 미실행. 이번 변경은 기존 토글 함수에 localStorage 저장/복원만 추가했으며, 새 route나 visual contract를 도입하지 않았으므로 browser smoke는 과했습니다.

## 남은 리스크
- localStorage가 차단된 환경(private browsing 등)에서는 preference가 저장되지 않지만, `try/catch`로 기존 동작은 유지됩니다.
- 다른 브라우저/기기 간 동기화는 없습니다. browser-local 설계이므로 의도된 제한입니다.
- `controller/assets/generated/bg-office.png` duplicate copy는 여전히 live contract 밖에 남아 있습니다.
