STATUS: implement

완료 슬라이스: `legacy shell keyboard focus-visible feedback`

근거 pair:
- latest `/work`: `work/4/2/2026-04-02-keyboard-focus-visible-feedback.md`
- latest same-day `/verify`: (아직 없음)

operator 결정 기록:
- React frontend → parked
- parallel stress hardening → current shipped single-worker 바깥, next 아님

이번 slice 범위:
- `app/static/style.css` — buttons, inputs, textarea, select에 `:focus-visible` 아웃라인 추가 (CSS-only, 3곳)
- JS/HTML/backend 변경 없음

검증:
- `파일 요약 후 근거와 요약 구간이 보입니다` targeted e2e — passed
- CSS-only이므로 full e2e 불필요
