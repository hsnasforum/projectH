# projectH 조사형 웹 파이프라인 초안

- 작성일: 2026-03-26
- 문서 상태: Draft
- 목적: 웹 검색 품질을 `검색 요약기`에서 `조사형 파이프라인`으로 재정의

## 1. 이 문서의 역할

이 문서는 [projecth-direction-reset-draft.md](/home/xpdlqj/code/projectH/docs/projectfile/projecth-direction-reset-draft.md)의 방향성을 실제 구현 순서로 내리는 보조 초안입니다.

핵심 질문은 하나입니다.

> projectH의 웹 검색 답변을 어떻게 “앞에 나온 문장 몇 개 요약”이 아니라 “조사 후 합의된 사실만 말하는 파이프라인”으로 바꿀 것인가?

## 2. 닫아야 할 첫 루프

가장 먼저 닫아야 할 루프는 아래입니다.

1. 질문
2. 분류
3. 검색
4. 출처 등급화
5. claim 추출
6. 충돌/합의 판정
7. 템플릿 출력
8. 평가 저장

지금 저장소는 이미 `app / core / tools / storage / model_adapter` 구조와 첫 세로 흐름을 갖고 있습니다.  
따라서 웹 검색도 거대한 새 시스템이 아니라, **두 번째 세로 흐름**으로 작게 닫는 것이 맞습니다.

## 3. 현재 상태에서 재사용할 것

이미 있는 것:

- `core/request_intents.py`
  - `none / explicit_web / live_latest / external_fact`
- `tools/web_search.py`
  - 검색 결과 수집
  - 원문 fetch
  - 도메인별 노이즈 정제
- `core/web_claims.py`
  - claim 구조
  - slot coverage 요약
- `storage/web_search_store.py`
  - 로컬 JSON 검색 기록 저장
- `tests/test_smoke.py`, `tests/test_web_app.py`
  - 웹 검색 회귀 기반

즉 지금 필요한 것은 전면 재작성보다, **의사결정 계층과 합의 계층을 명확히 분리하는 것**입니다.

## 4. 가장 먼저 바꿔야 할 것

### 4.1 분류기 확장

`kind`를 계속 늘리기보다 아래 두 필드를 추가합니다.

- `freshness_risk: low | high`
- `answer_mode: entity_card | latest_update | general`

### 4.2 기본 규칙

- `live_latest`면 무조건
  - `freshness_risk=high`
  - `answer_mode=latest_update`
- `external_fact`인데 아래 단어가 있으면
  - `출시`
  - `발표`
  - `예정`
  - `플랫폼`
  - `버전`
  - `가격`
  - `CEO`
  - `일정`
  - `신작`
  역시 `high`
- 나머지 소개형은
  - `freshness_risk=low`
  - `answer_mode=entity_card`

## 5. 출처 정책 분리

새 파일:

- [source_policy.py](/home/xpdlqj/code/projectH/core/source_policy.py)

여기서만 출처를 분류하고 점수화합니다.

### 출처 타입

- `official`
- `database`
- `news`
- `wiki`
- `community`

### 하드 룰

1. `high risk` 질문에서는 `wiki/community` 단독으로
   - 출시일
   - 플랫폼
   - 상태
   - 가격
   - 버전
   - 직함
   을 채우지 않습니다.
2. 공식 출처가 있으면 공식 출처를 우선합니다.
3. 공식 출처가 없으면 **독립된 2개 이상 출처 합의**가 있을 때만 채웁니다.
4. 그 외에는 `미확정`으로 둡니다.

## 6. Claim 스키마

초기 슬롯은 6개만 씁니다.

- `one_liner`
- `status`
- `developer_or_publisher`
- `platform`
- `release`
- `genre`

예시:

```python
@dataclass
class Claim:
    slot: str
    value: str
    source_type: str
    source_url: str
    source_title: str
    confidence: float
    freshness_sensitive: bool
```

현재 [web_claims.py](/home/xpdlqj/code/projectH/core/web_claims.py)의 구조를 완전히 버릴 필요는 없고,  
위 개념에 맞게 `slot/value/source_type/confidence` 중심으로 정리하면 됩니다.

## 7. 충돌 판정기 분리

새 파일:

- [claim_resolver.py](/home/xpdlqj/code/projectH/core/claim_resolver.py)

여기서 판정 규칙을 명확히 합니다.

### 최소 판정 규칙

- 같은 슬롯, 같은 값, 독립 출처 2건 이상 → 채택
- 공식 출처 1건 → 채택
- 값 충돌, 공식 없음 → 미확정
- 약한 출처 1건뿐 → 미채택 또는 불확실

원칙은 하나입니다.

> 빈칸보다 오답이 더 나쁩니다.

## 8. 답변 템플릿

설명형 답변은 두 가지 템플릿만 먼저 운영합니다.

### 8.1 entity_card

- 한 줄 정의
- 핵심 사실
- 근거 출처

### 8.2 latest_update

- 현재 확인된 점
- 아직 미정인 점
- 근거 출처

핵심은 모든 질문을 `entity_card`처럼 처리하지 않는 것입니다.  
예: `바이오하자드 레퀴엠이 뭐야?`는 겉으로는 엔티티 설명이지만, 실제로는 `latest_update`에 더 가깝습니다.

## 9. 평가 저장

새 저장 파일:

- `/home/xpdlqj/code/projectH/data/evals/web_cases.jsonl`

처음에는 이 파일 하나만 있어도 충분합니다.

### 저장 필드

- `question`
- `intent_kind`
- `freshness_risk`
- `selected_sources`
- `claims_before_merge`
- `final_answer`
- `human_label`
- `failure_reason`

### failure_reason 표준

- `factual_error`
- `freshness_error`
- `source_priority_error`
- `context_miss`
- `tone_issue`

## 10. 구현 흐름

얇은 오케스트레이션은 아래처럼 유지합니다.

```python
decision = classify_request(text)              # kind, query, freshness_risk, answer_mode
results = search_web(expand_queries(decision))
sources = rank_sources(results, decision)
claims = extract_claims(sources[:5], decision)
resolved = resolve_claims(claims, decision)
answer = render_answer(resolved, decision)
save_eval_case(decision, sources, claims, answer)
```

핵심은 `모델 자유 생성`보다 `claim 추출 -> 합의 -> 템플릿 출력`이 먼저라는 점입니다.

## 11. UI 반영 범위

UI는 크게 새로 만들 필요가 없습니다.

이미 있는 요소:

- response origin 배지
- 근거 패널
- 세션 타임라인
- 검색 기록 패널
- 사실 검증 상태 패널

여기에 아래만 추가하면 됩니다.

- `source_type`
- `support_count`
- `confidence`
- `미확정` 표시

즉 지금 필요한 것은 “새 UI”가 아니라 **정보 밀도와 신뢰도 표시를 정직하게 만드는 것**입니다.

## 12. 오늘 바로 할 커밋 3개

### Commit 1

- [request_intents.py](/home/xpdlqj/code/projectH/core/request_intents.py)에
  - `freshness_risk`
  - `answer_mode`
  추가

### Commit 2

- [source_policy.py](/home/xpdlqj/code/projectH/core/source_policy.py) 신설
- 현재의 `wiki > official`처럼 보일 수 있는 우선순위 제거

### Commit 3

- `latest_update` 템플릿 추가
- `web_cases.jsonl` 로깅 추가

이 세 가지가 먼저 붙어야, 모델을 바꾸더라도 **무엇이 좋아졌는지 측정**할 수 있습니다.

## 13. 1차 수용 기준

다음 조건을 통과하면 1차 성공으로 봅니다.

1. 위키 1건만으로 민감 슬롯을 채우지 않습니다.
2. 출처 충돌 시 `미확정`으로 남깁니다.
3. 최신성 높은 질문은 `latest_update` 템플릿을 사용합니다.
4. 답변마다 어떤 출처 타입을 썼는지 남깁니다.
5. 평가 케이스가 `jsonl`로 누적됩니다.

## 14. 결론

지금 projectH에 필요한 것은 더 큰 모델이 아니라, **질문 → 분류 → 검색 → claim → 합의 → 템플릿 → 평가**로 닫히는 품질 루프입니다.

즉, 다음 단계는 “웹 검색 답변을 더 그럴듯하게 만들기”가 아니라:

- `freshness_risk`
- `answer_mode`
- `source_policy`
- `claim_resolver`
- `web_cases.jsonl`

을 기준으로 **조사형 파이프라인을 작게 닫는 것**입니다.
