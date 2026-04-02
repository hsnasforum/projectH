# 2026-04-02 response-box header semantics cleanup

**범위**: legacy shell response-box 헤더 텍스트를 transcript=본문, response-box=컨트롤 패널이라는 역할에 맞게 조정
**근거**: `work/4/2/2026-04-02-response-box-transcript-duplication-cleanup.md`에서 response text를 visually hidden 처리한 후, 헤더 "응답"이 컨트롤 패널 역할과 맞지 않음

---

## 변경 파일

- `app/templates/index.html` — response-box 헤더 텍스트 2건 변경

---

## 사용 skill

- 없음

---

## 변경 이유

이전 라운드에서 `#response-text`를 visually hidden으로 처리하여 transcript card가 본문 표시의 canonical surface가 되었다. 그러나 response-box 헤더는 여전히 "응답"으로 되어 있어, 마치 응답 본문을 표시하는 패널인 것처럼 보였다. 컨트롤/메타 패널로서의 역할을 명확히 하기 위해 헤더 텍스트를 조정.

---

## 핵심 변경

- 섹션 타이틀: "응답" → "응답 도구"
- 복사 버튼 라벨: "응답 복사" → "본문 복사"
- JS의 copy 성공 notice("응답 텍스트를 복사했습니다.")는 변경하지 않음 (e2e 테스트 검증 대상)

---

## 검증

- targeted: `파일 요약 후 근거와 요약 구간이 보입니다` — **passed**
- `make e2e-test` — **16/16 passed**

---

## 남은 리스크

- 없음. HTML-only 텍스트 변경이며 기능 영향 없음.
