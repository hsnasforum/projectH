# Playwright Smoke

이 디렉터리는 로컬 웹 셸의 데모용 브라우저 스모크를 담습니다.

## 전제조건

- `node`, `npm`, `npx`가 설치되어 있어야 합니다.
- WSL 또는 Linux 환경에서 `python3`로 `app.web`를 실행할 수 있어야 합니다.

## 설치

```bash
cd /home/xpdlqj/code/projectH/e2e
npm install
npx playwright install
```

## 실행

```bash
cd /home/xpdlqj/code/projectH/e2e
npm test
```

또는 저장소 루트에서:

```bash
cd /home/xpdlqj/code/projectH
make e2e-test
```

## 포함된 시나리오

1. 파일 요약 후 근거/요약 구간 패널 확인
2. 브라우저 파일 선택으로 로컬 파일 요약
3. 브라우저 폴더 선택으로 문서 검색
4. 승인 카드에서 저장 경로 수정 후 새 approval 발급
5. 승인 후 실제 note 저장
6. explicit original-draft save 이후 late flip: saved history 유지 -> latest content verdict만 `rejected`로 변경
7. `내용 거절` content-verdict path: response-card action -> same-card reject-note update -> pending approval 유지 -> later explicit save supersession
8. corrected-save first bridge path: disabled-helper -> 수정본 기록 -> frozen approval snapshot -> immutable save
9. corrected-save long history chain: corrected-save 저장 -> late reject -> later re-correct, while saved corrected snapshot stays unchanged
10. candidate-linked explicit confirmation path: response-card action -> approval surface와 분리 유지 -> same source message의 `candidate_confirmation_record` 기록 -> save support와 별도 trace 유지 -> later correction으로 current state clear
11. 스트리밍 중 취소 버튼 동작

## 현재 기준

- WSL 환경에서 실제 실행 확인을 마쳤습니다.
- 자동화는 `mock` 프로바이더 기준으로 고정되어 있습니다.
- Playwright webServer는 inherited `LOCAL_AI_MODEL_PROVIDER` / `LOCAL_AI_OLLAMA_MODEL` 값을 먼저 비우고 `LOCAL_AI_MODEL_PROVIDER=mock`를 다시 강제하며, smoke 포트의 기존 서버도 재사용하지 않습니다. 따라서 셸에 `LOCAL_AI_MODEL_PROVIDER=ollama`가 남아 있어도 smoke baseline은 바뀌지 않습니다.
- `ollama` 경로는 품질과 속도 편차가 있어 수동 확인 체크리스트로 유지합니다.
