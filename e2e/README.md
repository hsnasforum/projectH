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
3. 승인 카드에서 저장 경로 수정 후 새 approval 발급
4. 승인 후 실제 note 저장
5. 스트리밍 중 취소 버튼 동작

## 현재 기준

- WSL 환경에서 실제 실행 확인을 마쳤습니다.
- 자동화는 `mock` 프로바이더 기준으로 고정되어 있습니다.
- `ollama` 경로는 품질과 속도 편차가 있어 수동 확인 체크리스트로 유지합니다.
