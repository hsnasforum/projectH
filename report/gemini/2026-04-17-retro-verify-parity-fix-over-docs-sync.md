# 2026-04-17-retro-verify-parity-fix-over-docs-sync

## 상황
- `seq 266`의 오퍼레이터 정지가 해당 블로커(`sendRequest` 시퀀싱 fix)의 검증 완료로 해제됨.
- 현재 트리에는 제품 코드(`core/agent_loop.py`) 변경이 포함된 미검증 `/work`와, 24개 시나리오 문서 동기화 위주의 미검증 `/work`가 공존함.
- `gemini_request.md`는 다음 단계로 또 다른 retro-verify를 수행할지, 아니면 새로운 구현 슬라이스를 열지 결정을 요청함.

## 후보 비교
1. **`work/4/17/2026-04-17-sqlite-entity-noisy-natural-reload-followup-parity-fix.md` (seq 248)**:
   - `core/agent_loop.py`의 핵심 비즈니스 로직 수정 포함.
   - SQLite 백엔드에서 자연어 reload 후 follow-up 시 요약 정보가 소실되던(모의 응답으로 덮어써지던) 중대한 패리티 결함 해결.
   - 서비스 레이어 regression 테스트(`tests/test_web_app.py`)가 추가되었으나 아직 `/verify`가 없음.
2. **`work/4/17/2026-04-17-sqlite-browser-history-card-natural-reload-chain-parity.md` (seq 249)**:
   - 24개 SQLite 브라우저 게이트 시나리오 실측 및 문서(README, docs/*) 동기화.
   - 제품 코드 변경은 없으며, 위 `parity-fix`가 정상 작동함을 전제로 함.

## 판단
- `GEMINI.md`의 우선순위에 따라 "same-family current-risk reduction"을 최우선으로 함.
- 제품 코드(Python)가 직접 수정된 `sqlite-entity-noisy-natural-reload-followup-parity-fix`를 먼저 검증하여 백엔드 로직의 무결성을 확정하는 것이 가장 시급함.
- 이 로직이 검증되어야 그 위에 쌓인 24개 시나리오 번들(`natural-reload-chain-parity`)의 실측 결과도 진실성을 가질 수 있음.

## 권고
- **RECOMMEND: retro-verify work/4/17/2026-04-17-sqlite-entity-noisy-natural-reload-followup-parity-fix.md**
- 새로운 구현 슬라이스를 열기 전, 이미 적용된 핵심 제품 fix의 무결성을 먼저 `/verify`로 잠글 것을 권장함.
