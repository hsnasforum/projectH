# 2026-04-17-retro-verify-sequencing-over-implementation

## 상황
- `seq 263`에서 발생한 미검증 `/work` 블로커가 최신 `noisy-single-source-strong-plus-missing-click-reload` 라운드 검증으로 해소됨.
- 그러나 트리 내에 제품 코드(JS, Python)가 변경되었으나 아직 `/verify`가 없는 과거 `/work`들이 존재함.
- `gemini_request.md`는 새로운 구현 슬라이스를 열지, 아니면 기존 미검증 제품 변경 건을 retro-verify할지 결정을 요청함.

## 후보 비교
1. **`work/4/17/2026-04-17-browser-history-card-sendrequest-followup-sequencing.md` (seq 250)**:
   - `app/static/app.js`의 핵심 통신 레이어에 `promise-queue` 도입.
   - 브라우저 테스트의 결정성(race condition 해결)을 보장하는 기초 공사.
   - 제품 전체의 UI 응답성 및 안정성에 영향을 주는 가장 근본적인 변경.
2. **`work/4/17/2026-04-17-sqlite-entity-noisy-natural-reload-followup-parity-fix.md` (seq 248)**:
   - `core/agent_loop.py`에서 특정 검색 시나리오(noisy single-source)의 요약 유지 로직 수정.
   - SQLite 백엔드 드리프트 해결을 위한 특정 기능 수정.

## 판단
- `GEMINI.md`의 우선순위에 따라 "same-family current-risk reduction"을 최우선으로 함.
- 새로운 구현 슬라이스를 열기 전에, 현재 모든 브라우저 기반 테스트 통과의 신뢰성 기반이 되는 `sendRequest` 시퀀싱 로직을 먼저 검증하여 "진실의 사슬"을 복구하는 것이 가장 안전함.
- 해당 변경이 실사용자 환경(UI double-submit 차단, 취소 세만틱 등)에 의도치 않은 회귀를 일으키지 않았는지 명시적으로 검증하고 닫는 과정이 필요함.

## 권고
- **RECOMMEND: retro-verify work/4/17/2026-04-17-browser-history-card-sendrequest-followup-sequencing.md**
- 새로운 기능 구현이나 다른 파생 작업으로 넘어가기 전, 핵심 비즈니스 로직(JS 통신 큐)의 무결성을 먼저 확정할 것을 권장함.
