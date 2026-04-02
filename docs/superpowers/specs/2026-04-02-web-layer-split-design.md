# web.py 계층별 분리 설계

**작성일**: 2026-04-02
**목표**: app/web.py 7,000줄을 책임별로 분리하여 유지보수성 확보

## 현황

`WebAppService` 클래스에 144개 메서드가 단일 파일에 존재:
- 직렬화(serialize): 25개
- 비즈니스 핸들러: 12개 (submit/emit/apply/confirm/stop/reverse)
- 채팅 코어: handle_chat, stream_chat, _handle_chat_impl
- 유틸리티: build, parse, normalize 등

## 분리 전략

### Phase 1: 클래스 유지 + mixin 분리 (이번 작업)

`WebAppService`를 유지하면서 메서드를 파일별로 분리. Python mixin 패턴 사용.

```
app/
├── web.py              → WebAppService 본체 + 라우트 등록 (~800줄)
├── serializers.py      → SerializerMixin (25개 _serialize_* 메서드)
├── handlers/
│   ├── __init__.py
│   ├── chat.py         → ChatHandlerMixin (handle_chat, stream_chat, _handle_chat_impl + 관련 private)
│   ├── feedback.py     → FeedbackHandlerMixin (submit_feedback, submit_correction, content_verdict, content_reason_note)
│   ├── preferences.py  → PreferenceHandlerMixin (list, activate, pause, reject)
│   └── aggregate.py    → AggregateHandlerMixin (candidate_confirmation, candidate_review, 5개 aggregate 트랜지션)
└── main.py             → 변경 없음
```

**WebAppService 상속 체인:**
```python
class WebAppService(
    ChatHandlerMixin,
    FeedbackHandlerMixin,
    PreferenceHandlerMixin,
    AggregateHandlerMixin,
    SerializerMixin,
):
    def __init__(self, settings, ...): ...
    # 라우트 등록, 초기화, 유틸리티만 남김
```

### Phase 2: 점진적 독립 함수 전환 (D→B→A 진행 중)

새로 추가하는 기능은 독립 함수 스타일로 작성. 기존 mixin도 기회 있을 때 전환.

## 파일별 예상 크기

| 파일 | 예상 줄 수 | 내용 |
|------|-----------|------|
| web.py | ~800 | __init__, 라우트 등록, 유틸리티 (build_*, parse_*, normalize_*) |
| serializers.py | ~900 | 25개 _serialize_* 메서드 |
| handlers/chat.py | ~2,500 | handle_chat, stream_chat, _handle_chat_impl + 스트리밍 워커 |
| handlers/feedback.py | ~600 | feedback, correction, verdict, reason_note |
| handlers/preferences.py | ~200 | preference CRUD 4개 |
| handlers/aggregate.py | ~1,500 | candidate + aggregate 트랜지션 7개 |

## 제약

- 기존 테스트 186개가 깨지지 않아야 함
- `self.session_store`, `self.task_logger` 등 내부 참조 유지
- import 순환 방지: mixin은 web.py를 import하지 않음
- 외부 API (라우트 경로, 요청/응답 형태) 변경 없음

## 성공 기준

1. web.py 800줄 이하
2. 기존 테스트 전체 통과
3. 서버 정상 기동 (python -m app.web)
