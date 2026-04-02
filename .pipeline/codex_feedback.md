STATUS: implement

완료 슬라이스: `legacy shell subtle button hover feedback`

근거 pair:
- latest `/work`: `work/4/2/2026-04-02-subtle-button-hover-feedback.md`
- latest same-day `/verify`: (아직 없음)

operator 결정 기록:
- React frontend → parked (repo에 남김, 연결/제거 안 함)
- parallel stress hardening → current shipped single-worker 바깥, 이번 기본 next로 올리지 않음
- 다음 slice → legacy shell canonical surface 안 가장 작은 user-visible polish

이번 slice 범위:
- `app/static/style.css` — subtle 버튼(`.copy-button.subtle`, `.toggle-button.subtle`, `.icon-button.subtle`) hover 피드백 추가 (CSS-only)
- JS/HTML/backend 변경 없음

검증:
- `파일 요약 후 근거와 요약 구간이 보입니다` targeted e2e — passed
- CSS-only이므로 full e2e 불필요
