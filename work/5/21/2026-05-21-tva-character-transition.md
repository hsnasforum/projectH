# 2026-05-21 TVA character transition

## 변경 파일

- `controller/assets/generated/codex_tva.png` [NEW]
- `controller/assets/generated/claude_tva.png` [NEW]
- `controller/assets/generated/gemini_tva.png` [NEW]
- `controller/js/cozy.js` [MODIFY]
- `work/5/21/2026-05-21-tva-character-transition.md` [NEW]

## 사용 skill

- `work-log-closeout`: 변경 내용, 검증 결과 및 잔존 리스크를 한국어 `/work` 닫기 기록으로 남기는 데 사용했습니다.

## 변경 이유

- 파이프라인 모니터링 화면(Cozy RPG 뷰) 내 에이전트 캐릭터(Codex, Claude, Gemini)를 픽셀 아트 스타일에서 더 화려하고 현대적인 느낌의 고품질 TVA 애니메이션 그림체 캐릭터로 전환해달라는 사용자 요청을 충족하기 위함입니다.

## 핵심 변경

- **크로마키 캔버스 헬퍼 도입**: 이미지의 좌상단 `(0,0)` 픽셀 색상값(네온 그린)을 읽어와 이와 유사한 초록색 영역을 알파 채널 `0`으로 처리하고, 경계면은 안티앨리어싱을 통해 투명하게 렌더링해 주는 `chromaKeyImage(img)` 함수를 추가하였습니다.
- **이미지 사전 로드 및 캐시 구축**: 웹 화면 로드 시 세 에이전트의 이미지 `/controller-assets/generated/*_tva.png`를 비동기로 읽어 들여 투명 처리된 오프스크린 캔버스로 변환 및 `AGENT_IMAGES` 구조체에 캐시하도록 설계했습니다.
- **drawAgent(a) 렌더링 대체**:
  - `drawAgent(a)` 안에서 이미지 캐시가 존재할 때 기존 픽셀 드로잉 대신 `drawImage`를 통해 캐릭터를 그리도록 변경했습니다.
  - 캐릭터의 좌우 방향(`facingRight`), 작업 시/대기 시 상하 바운싱(`bob`), 그리고 에이전트가 중지/사망 상태일 때 90도 회전(fainted felling)되는 모션을 local matrix transform(`translate`, `scale`, `rotate`)을 사용해 일괄 구현하였습니다.
  - 이미지가 로딩되는 과정이나 커스텀 에이전트가 생성되는 케이스를 고려하여, 캐싱되지 않은 경우에는 기존의 JRPG 픽셀 캐릭터로 안전하게 fallback 그리기하도록 보완했습니다.

## 검증

- **Playwright E2E 테스트 실행**:
  - `wsl make controller-test`
  - 결과: 전체 20개 테스트 모두 성공적으로 통과 (`20 passed (37.5s)`).
  - Canvas 렌더링 및 모니터 서버 통신 시 오동작이나 UI 붕괴 현상이 없음을 확인했습니다.

## 남은 리스크

- 일러스트 이미지 로딩 시, 네트워크 환경에 따라 첫 로드 완료 전 수 초 동안은 fallback 픽셀 캐릭터가 렌더링될 수 있습니다.
- 크로마키 감지 방식은 좌상단 `(0,0)`의 픽셀 단색을 기준으로 비교하므로, 이미지 생성 시 미세한 노이즈나 압축 아티팩트로 경계면 바깥쪽의 색상이 변질된 경우 극히 일부 잔여 테두리가 남을 수 있으나 현재 생성된 이미지 품질은 극히 우수함을 확인했습니다.
- commit, push, PR, merge는 임베디드 오토메이션 제약에 따라 수행하지 않고 로컬 변경 상태로 남겨둡니다.
