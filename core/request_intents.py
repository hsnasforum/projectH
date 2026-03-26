from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Literal


SearchIntentKind = Literal["none", "explicit_web", "live_latest", "external_fact"]


@dataclass(frozen=True, slots=True)
class SearchIntentDecision:
    kind: SearchIntentKind = "none"
    query: str | None = None
    score: int = 0
    reasons: tuple[str, ...] = ()
    suggestion_kind: SearchIntentKind = "none"
    suggestion_query: str | None = None
    suggestion_score: int = 0
    suggestion_reasons: tuple[str, ...] = ()


_DIRECT_WEB_MARKERS = (
    "웹 검색",
    "웹검색",
    "인터넷에서",
    "온라인에서",
)

_LOCAL_DOCUMENT_HINTS = (
    "이 문서",
    "현재 문서",
    "문서에서",
    "파일에서",
    "이 파일",
    "로컬 문서",
    "내 문서",
    "내 파일",
    "검색 결과에서",
)

_IMPLICIT_WEB_SEARCH_BLOCKERS = (
    "문서",
    "파일",
    "본문",
    "요약",
    "메모",
    "로컬",
)

_LIVE_INFO_KEYWORDS = (
    "날씨",
    "기온",
    "비 와",
    "비와",
    "눈 와",
    "눈와",
    "실시간",
    "지금 뉴스",
    "속보",
    "오늘 뉴스",
    "환율",
    "주가",
    "시세",
)

_LATEST_INFO_KEYWORDS = (
    "최신",
    "최근",
    "요즘",
    "근황",
    "소식",
    "업데이트",
    "일정",
    "신곡",
    "새 앨범",
    "앨범",
    "콘서트",
    "공연",
    "투어",
    "개봉",
    "예매",
    "이슈",
)

_IMPLICIT_WEB_SEARCH_ACTION_HINTS = (
    "어때",
    "알려줘",
    "알려주세요",
    "정리해줘",
    "정리해주세요",
    "보여줘",
    "보여주세요",
    "궁금해",
    "궁금해요",
    "있어",
    "있어요",
    "있나",
    "있나요",
    "뭐야",
    "뭐예요",
)

_EXPLICIT_WEB_SEARCH_SUFFIX_RE = re.compile(
    r"("
    r"(?:검색(?:\s*좀)?|좀\s*검색)(?:해(?:봐|줘|주세요|요|줄래|주실래)?|해\s*(?:봐|줘|주세요|요|줄래|주실래)|해봐|해줘|해주세요|해요)?"
    r"|검색해(?:봐|줘|주세요|요|줄래|주실래)?"
    r"|찾아(?:봐|줘|주세요|요|와|와줘|와주세요|와줄래|볼래|봐줘|봐주세요|봐줄래|봐주실래)"
    r"|찾아\s*(?:봐|줘|주세요|요|와|와줘|와주세요|와줄래|볼래|봐줘|봐주세요|봐줄래|봐주실래)"
    r"|알아(?:봐|봐줘|봐주세요|봐줄래|봐주실래|와|와줘|와주세요|와줄래)"
    r"|알아\s*(?:봐|봐줘|봐주세요|봐줄래|봐주실래|와|와줘|와주세요|와줄래)"
    r"|관련해서\s*(?:좀\s*)?(?:볼래|봐줘|봐주세요|봐줄래|봐주실래|정리해줘|알려줘)"
    r")([?!.]+)?$"
)

_EXPLICIT_WEB_SEARCH_CLEANUP_PATTERNS = [
    r"웹\s*검색(을|좀)?\s*",
    r"인터넷에서\s*",
    r"온라인에서\s*",
    r"검색\s*좀\s*해(?:봐|줘|주세요|요|줄래|주실래)?$",
    r"좀\s*검색(?:해(?:봐|줘|주세요|요|줄래|주실래)?)?$",
    r"검색해요?$",
    r"검색해\s*요?$",
    r"검색해\s*봐요?$",
    r"검색해\s*줘요?$",
    r"검색해\s*줄래$",
    r"검색해\s*주실래$",
    r"검색해\s*주세요$",
    r"검색$",
    r"찾아\s*봐요?$",
    r"찾아\s*줘요?$",
    r"찾아\s*줄래$",
    r"찾아\s*주실래$",
    r"찾아\s*와$",
    r"찾아\s*와줘$",
    r"찾아\s*와주세요$",
    r"찾아\s*와줄래$",
    r"찾아\s*볼래$",
    r"찾아\s*봐줄래$",
    r"찾아\s*봐줘$",
    r"찾아\s*봐주세요$",
    r"찾아\s*봐주실래$",
    r"찾아\s*주세요$",
    r"알아\s*봐요?$",
    r"알아\s*봐줘$",
    r"알아\s*봐주세요$",
    r"알아\s*봐줄래$",
    r"알아\s*봐주실래$",
    r"알아\s*와$",
    r"알아\s*와줘$",
    r"알아\s*와주세요$",
    r"알아\s*와줄래$",
    r"알아\s*주세요$",
    r"관련해서\s*(?:좀\s*)?(?:볼래|봐줘|봐주세요|봐줄래|봐주실래|정리해줘|알려줘)$",
]

_IMPLICIT_WEB_SEARCH_CLEANUP_PATTERNS = [
    r"\s*알려\s*줘요?$",
    r"\s*알려\s*주세요$",
    r"\s*정리해\s*줘요?$",
    r"\s*정리해\s*주세요$",
    r"\s*보여\s*줘요?$",
    r"\s*보여\s*주세요$",
    r"\s*궁금해요?$",
    r"\s*어때(?:요)?$",
    r"\s*있나요?$",
    r"\s*있어요?$",
    r"\s*있나$",
    r"\s*뭐예요?$",
    r"\s*뭐야$",
]

_EXTERNAL_FACT_SUFFIX_SIGNALS: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:에 대해|에대한|에 관한|에관한)\s*"
            r"(?:알려줘|알려\s*주세요|알려주세요|설명해줘|설명해\s*주세요|설명해주세요|소개해줘|소개해\s*주세요|소개해주세요|정리해줘|정리해\s*주세요|정리해주세요|궁금한데|궁금한데요|알고\s*싶어|알고\s*싶어요)\??$"
        ),
        5,
        "topic_request",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:은|는|이|가)?\s*"
            r"(?:누구야|누구예요|누구인가요|누구임|뭐야|뭐예요|뭐임|무엇이야|무엇인가요|"
            r"어떤\s*(?:사람|분|게임|서비스)(?:이야|인가요|임)|"
            r"무슨\s*(?:게임|서비스|제품|사이트|회사|인물)(?:이야|인가요|임)|"
            r"뭐하는\s*(?:사람|분|게임|곳)(?:이야|인가요|임))\??$"
        ),
        5,
        "identity_question",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:은|는|이|가)?\s*"
            r"(?:누군지|뭔지|무엇인지|어떤\s*(?:사람|분|게임|서비스)인지|무슨\s*(?:게임|서비스|제품|사이트|회사|인물)인지|뭐하는\s*(?:사람|분|게임|곳)인지)\s*"
            r"(?:궁금해|궁금해요|궁금한데|궁금한데요|알고\s*싶어|알고\s*싶어요|알려줘|알려\s*주세요|알려주세요)?\??$"
        ),
        4,
        "identity_curiosity",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:은|는|이|가)?\s*(?:좀\s*)?"
            r"(?:알려줘|알려\s*주세요|알려주세요|정리해줘|정리해\s*주세요|정리해주세요|설명해줘|설명해\s*주세요|설명해주세요|소개해줘|소개해\s*주세요|소개해주세요)\??$"
        ),
        3,
        "generic_info_request",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:은|는|이|가)?\s*(?:아냐|알아|아나요|알아요)\??$"
        ),
        2,
        "know_question",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:얘기|이야기)\s*(?:좀\s*)?"
            r"(?:해줘|해\s*줘|해\s*주세요|해주세요|해봐|해\s*봐|들려줘|들려\s*줘|들려\s*주세요|들려주세요)\??$"
        ),
        3,
        "story_request",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*관련(?:된)?\s*(?:거|정보|내용|얘기|이야기)\s*(?:좀\s*)?"
            r"(?:있어|있어요|있나|있나요|알려줘|알려\s*주세요|알려주세요|정리해줘|정리해\s*주세요|정리해주세요)?\??$"
        ),
        3,
        "related_info_request",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*쪽(?:은|은요)?\s*(?:어때|어때요)\??$"
        ),
        2,
        "side_question",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*쪽으로\s*(?:좀\s*)?(?:봐줘|봐\s*주세요|봐줄래|봐주실래)\??$"
        ),
        3,
        "side_review_request",
    ),
)

_EXTERNAL_FACT_SOFT_SIGNALS: tuple[tuple[re.Pattern[str], int, str], ...] = (
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:궁금해|궁금해요|궁금한데|궁금한데요|알고\s*싶어|알고\s*싶어요)\??$"
        ),
        1,
        "soft_curiosity",
    ),
    (
        re.compile(
            r"^(?P<query>.+?)\s*(?:어때|어때요)\??$"
        ),
        1,
        "soft_opinion",
    ),
)


def normalize_user_text(user_text: str | None) -> str:
    if not isinstance(user_text, str):
        return ""
    trimmed = user_text.strip()
    retry_split_marker = "\n\n방금 답변은 "
    if retry_split_marker in trimmed:
        trimmed = trimmed.split(retry_split_marker, 1)[0].strip()
    normalized = " ".join(trimmed.split())
    return re.sub(r"\s+([?!.])", r"\1", normalized)


def _dedupe_reasons(reasons: list[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for reason in reasons:
        if reason in seen:
            continue
        seen.add(reason)
        ordered.append(reason)
    return tuple(ordered)


def _clean_with_patterns(text: str, patterns: list[str]) -> str:
    cleaned = re.sub(r"[?!.]+$", "", text).strip()
    for pattern in patterns:
        cleaned = re.sub(pattern, " ", cleaned)
    cleaned = re.sub(r"[?!.]+$", "", cleaned).strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


def _query_quality_score(query: str) -> tuple[int, list[str]]:
    cleaned = " ".join(query.split()).strip()
    score = 0
    reasons: list[str] = []
    if len(cleaned) >= 2:
        score += 1
        reasons.append("query_length")
    if re.search(r"[A-Za-z가-힣0-9]", cleaned):
        score += 1
        reasons.append("query_text")
    if 1 <= len(cleaned.split()) <= 6:
        score += 1
        reasons.append("query_compact")
    return score, reasons


def _has_local_document_hint(normalized: str) -> bool:
    return any(hint in normalized for hint in _LOCAL_DOCUMENT_HINTS)


def _has_implicit_blocker(normalized: str) -> bool:
    return any(blocker in normalized for blocker in _IMPLICIT_WEB_SEARCH_BLOCKERS)


def _extract_explicit_candidate(normalized: str) -> SearchIntentDecision:
    if not normalized:
        return SearchIntentDecision()

    if any(marker in normalized for marker in _DIRECT_WEB_MARKERS):
        cleaned = _clean_with_patterns(normalized, _EXPLICIT_WEB_SEARCH_CLEANUP_PATTERNS)
        query = cleaned or normalized
        return SearchIntentDecision(
            kind="explicit_web",
            query=query,
            score=12,
            reasons=("direct_marker", "explicit_cleanup"),
        )

    if _has_local_document_hint(normalized):
        return SearchIntentDecision()

    if not _EXPLICIT_WEB_SEARCH_SUFFIX_RE.search(normalized):
        return SearchIntentDecision()

    cleaned = _clean_with_patterns(normalized, _EXPLICIT_WEB_SEARCH_CLEANUP_PATTERNS)
    query = cleaned or normalized
    quality_score, quality_reasons = _query_quality_score(query)
    return SearchIntentDecision(
        kind="explicit_web",
        query=query,
        score=8 + quality_score,
        reasons=_dedupe_reasons(["explicit_suffix", *quality_reasons]),
    )


def _extract_live_latest_candidate(normalized: str) -> SearchIntentDecision:
    if not normalized or _has_local_document_hint(normalized) or _has_implicit_blocker(normalized):
        return SearchIntentDecision()

    live_hits = [keyword for keyword in _LIVE_INFO_KEYWORDS if keyword in normalized]
    latest_hits = [keyword for keyword in _LATEST_INFO_KEYWORDS if keyword in normalized]
    action_hits = [keyword for keyword in _IMPLICIT_WEB_SEARCH_ACTION_HINTS if keyword in normalized]

    score = 0
    reasons: list[str] = []
    if live_hits:
        score += 5
        reasons.append("live_topic")
    if latest_hits:
        score += 3
        reasons.append("latest_topic")
    if action_hits:
        score += 2
        reasons.append("action_hint")
    if score < 4:
        return SearchIntentDecision()

    cleaned = _clean_with_patterns(normalized, _IMPLICIT_WEB_SEARCH_CLEANUP_PATTERNS)
    cleaned = re.sub(r"(은|는|이|가)$", "", cleaned).strip()
    query = cleaned or normalized
    quality_score, quality_reasons = _query_quality_score(query)
    return SearchIntentDecision(
        kind="live_latest",
        query=query,
        score=score + quality_score,
        reasons=_dedupe_reasons([*reasons, *quality_reasons]),
    )


def _clean_external_fact_query(query: str) -> str:
    cleaned = " ".join(str(query or "").split()).strip()
    cleanup_patterns = [
        r"\s*(?:라는|이란|인)\s*(?:사이트|서비스|게임|인물|채널|회사|기업|브랜드)\s*$",
        r"\s+(?:사이트|서비스|게임|인물|채널|회사|기업|브랜드)\s*$",
        r"\s*(?:은|는|이|가)?\s*(?:누군지|뭔지|무엇인지|어떤\s*사람인지|어떤\s*분인지|어떤\s*게임인지|어떤\s*서비스인지|뭐하는\s*사람인지|뭐하는\s*분인지|뭐하는\s*게임인지|뭐하는\s*곳인지)\s*$",
        r"\s*관련(?:된)?\s*(?:거|정보|내용|얘기|이야기)\s*$",
        r"\s*(?:정보|내용|얘기|이야기)\s*$",
        r"\s*쪽\s*$",
        r"\s*쪽으로\s*$",
        r"\s*(?:대충|간단히|간단하게|짧게|한번만|좀)\s*$",
    ]
    for pattern in cleanup_patterns:
        cleaned = re.sub(pattern, "", cleaned).strip()
    cleaned = re.sub(r"(은|는|이|가|를|을)$", "", cleaned).strip()
    return cleaned


def _extract_external_fact_candidate(normalized: str) -> SearchIntentDecision:
    if not normalized or _has_local_document_hint(normalized) or _has_implicit_blocker(normalized):
        return SearchIntentDecision()

    best_query: str | None = None
    best_score = 0
    best_reasons: tuple[str, ...] = ()

    for pattern, base_score, reason in _EXTERNAL_FACT_SUFFIX_SIGNALS:
        match = pattern.match(normalized)
        if not match:
            continue
        query = _clean_external_fact_query(str(match.group("query") or ""))
        if len(query) < 2:
            continue
        quality_score, quality_reasons = _query_quality_score(query)
        score = base_score + quality_score
        reasons = _dedupe_reasons([reason, *quality_reasons])
        if score > best_score:
            best_query = query
            best_score = score
            best_reasons = reasons

    if not best_query or best_score < 4:
        return SearchIntentDecision()

    return SearchIntentDecision(
        kind="external_fact",
        query=best_query,
        score=best_score,
        reasons=best_reasons,
    )


def _extract_external_fact_suggestion(normalized: str) -> SearchIntentDecision:
    if not normalized or _has_local_document_hint(normalized) or _has_implicit_blocker(normalized):
        return SearchIntentDecision()

    best_query: str | None = None
    best_score = 0
    best_reasons: tuple[str, ...] = ()

    for pattern, base_score, reason in _EXTERNAL_FACT_SOFT_SIGNALS:
        match = pattern.match(normalized)
        if not match:
            continue
        query = _clean_external_fact_query(str(match.group("query") or ""))
        if len(query) < 2:
            continue
        quality_score, quality_reasons = _query_quality_score(query)
        score = base_score + quality_score
        reasons = _dedupe_reasons([reason, *quality_reasons])
        if score > best_score:
            best_query = query
            best_score = score
            best_reasons = reasons

    if not best_query or best_score < 3:
        return SearchIntentDecision()

    return SearchIntentDecision(
        suggestion_kind="external_fact",
        suggestion_query=best_query,
        suggestion_score=best_score,
        suggestion_reasons=best_reasons,
    )


def classify_search_intent(user_text: str | None) -> SearchIntentDecision:
    normalized = normalize_user_text(user_text)
    if not normalized:
        return SearchIntentDecision(reasons=("empty",))

    explicit_candidate = _extract_explicit_candidate(normalized)
    if explicit_candidate.kind == "explicit_web":
        return explicit_candidate

    if _has_local_document_hint(normalized):
        return SearchIntentDecision(reasons=("local_document_hint",))

    live_latest_candidate = _extract_live_latest_candidate(normalized)
    external_fact_candidate = _extract_external_fact_candidate(normalized)
    external_fact_suggestion = _extract_external_fact_suggestion(normalized)

    if live_latest_candidate.score >= external_fact_candidate.score and live_latest_candidate.kind != "none":
        return live_latest_candidate
    if external_fact_candidate.kind != "none":
        return external_fact_candidate
    if external_fact_suggestion.suggestion_query:
        return SearchIntentDecision(
            reasons=("low_confidence_web_candidate",),
            suggestion_kind=external_fact_suggestion.suggestion_kind,
            suggestion_query=external_fact_suggestion.suggestion_query,
            suggestion_score=external_fact_suggestion.suggestion_score,
            suggestion_reasons=external_fact_suggestion.suggestion_reasons,
        )
    return SearchIntentDecision(reasons=("no_web_intent_signal",))


def is_explicit_web_search_request(user_text: str | None) -> bool:
    return classify_search_intent(user_text).kind == "explicit_web"


def extract_explicit_web_search_query(user_text: str | None) -> str | None:
    decision = classify_search_intent(user_text)
    if decision.kind != "explicit_web":
        return None
    return decision.query


def looks_like_live_or_latest_info_request(user_text: str | None) -> bool:
    return classify_search_intent(user_text).kind == "live_latest"


def extract_implicit_web_search_query(user_text: str | None) -> str | None:
    decision = classify_search_intent(user_text)
    if decision.kind != "live_latest":
        return None
    return decision.query


def looks_like_external_fact_info_request(user_text: str | None) -> bool:
    return classify_search_intent(user_text).kind == "external_fact"


def extract_external_fact_query(user_text: str | None) -> str | None:
    decision = classify_search_intent(user_text)
    if decision.kind != "external_fact":
        return None
    return decision.query
